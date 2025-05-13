import logging
import uuid 

from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.responses import JSONResponse
from app.src.producer import Producer
from app.src.consumer import Consumer
from app.src.cosmos import CosmosDBClient
from app.config import settings
from contextlib import asynccontextmanager
from typing import Any
from azure.eventhub.extensions.checkpointstoreblobaio import BlobCheckpointStore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Checkpoint store for Event Hub
checkpoint_store = BlobCheckpointStore.from_connection_string(
    settings.STORAGE_ACCOUNT_CHECKPOINT_STORE,
    settings.STORAGE_ACCOUNT_CHECKPOINT_STORE_CONTAINER
    
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup would go here if needed
    yield
    # shutdown logic
    await producer.close()

app = FastAPI(
    title="Azure Event Hub API",
    version="1.0.0",
    description="API for sending events to Azure Event Hub",
    lifespan=lifespan
)

# Initialize Producer and Consumer
try:
    producer = Producer()
    consumer = Consumer(checkpoint_store=checkpoint_store)
    cosmos_client = CosmosDBClient()
    logger.info("Producer, Consumer, and CosmosDBClient were initialized successfully")
except Exception as err:
    logger.error(f"Failed to initialize the Producer/Consumer/CosmosDBClient: {err}")
    raise

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.get("/health", summary="Health check")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy"}

@app.post("/producer", summary="Send event to Event Hub")
async def send_event(payload: Any = Body(...)):
    """Receives raw JSON (dict or list) and sends events to Azure Event Hub"""

    try:
        # Determine if single or batch
        raw_events = payload if isinstance(payload, list) else [payload]

        request_ids = []

        # send each payload in its own batch
        for raw_evt in raw_events:
            # Generate a unique request ID
            request_id = str(uuid.uuid4())
            request_ids.append(request_id)

            # Prepare the event to send
            event_to_send = {"request_id": request_id, **raw_evt}

            # Send the event
            await producer.send_event(event_to_send)

        return {
            "request_ids": request_ids,
            "detail": f"{len(raw_events)} event(s) sent successfully"
        }
    except ValueError as ve:
        logger.warning(f"Validation error when sending event: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as ex:
        logger.error(f"Error sending event: {ex}")
        raise HTTPException(status_code=500, detail="Failed to send event")

@app.post("/consumer", summary="Consume event from Event Hub and process")
async def consume_event():
    """Consumes an event from Event Hub, checks metric, calls OpenAI, persists response, and marks event as processed."""
    processed_count = await consumer.consume_event()
    return {"Events Processed": processed_count}

@app.get("/response/{request_id}", summary="Get Azure OpenAI response by request_id")
async def get_openai_response(request_id: str):
    """Fetch the OpenAI response from CosmosDB by request_id."""
    try:
        doc = await cosmos_client.get_response_by_request_id(request_id)
        if doc is None:
            return {"status": "processing", "detail": "Request is still being processed or not found."}
        return {"status": "completed", "response": doc.get("openai_response")}
    except Exception as ex:
        logger.error(f"Error fetching response for request_id {request_id}: {ex}")
        raise HTTPException(status_code=500, detail="Failed to fetch response from CosmosDB")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8082,
        reload=True
    )
