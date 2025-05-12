import logging
import uuid 
import json

from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.responses import JSONResponse
from app.producer import Producer
from app.schemas import EventPayload, BatchEventPayload
from app.config import settings
import httpx
from azure.cosmos.aio import CosmosClient
from azure.eventhub.aio import EventHubConsumerClient
from azure.eventhub import EventData
from contextlib import asynccontextmanager
from typing import Union, Any
from azure.eventhub.extensions.checkpointstoreblobaio import BlobCheckpointStore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Checkpoint store for Event Hub
checkpoint_store = BlobCheckpointStore.from_connection_string(
    settings.STOREAGE_ACCOUNT_CHECKPOINT_STORE,
    settings.STOREAGE_ACCOUNT_CHECKPOINT_STORE_CONTAINER
    
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

# Initialize EventHub client
try:
    producer = Producer()
    logger.info("EventHub client initialized successfully")
    eventhub_client = producer  # alias for tests compatibility
except Exception as err:
    logger.error(f"Failed to initialize EventHub client: {err}")
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
    request_id = str(uuid.uuid4())
    try:
        # Determine if single or batch
        raw_events = payload if isinstance(payload, list) else [payload]
        # send each payload in its own batch
        for raw_evt in raw_events:
            messages = raw_evt.get("messages")
            if messages is None:
                raise ValueError("Missing 'messages' field in payload")
            event_to_send = {"request_id": request_id, "messages": messages}
            await producer.send_event(event_to_send)
        return {"request_id": request_id,
                "detail": f"{len(raw_events)} event(s) sent successfully"}
    except ValueError as ve:
        logger.warning(f"Validation error when sending event: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as ex:
        logger.error(f"Error sending event: {ex}")
        raise HTTPException(status_code=500, detail="Failed to send event")

# Helper: Get metric from Azure Monitor
async def get_openai_utilization():
    # This is a stub. You'd use Azure Monitor REST API here.
    # Return a float representing the utilization metric.
    # Example: Use httpx to call the Azure Monitor API with proper auth.
    # For now, return a dummy value for demonstration.
    return 0.3

# Helper: Call Azure OpenAI API
async def call_openai_api(messages):
    # This is a stub. You'd use httpx to call the OpenAI API.
    # Return the response as a dict.
    logger.info(f"Calling OpenAI API with messages: {messages}")
    return {"choices": [{"text": "OpenAI response"}]}

# Helper: Persist to CosmosDB
async def persist_to_cosmos(request_id, openai_response):
    # This is a stub. You'd use CosmosClient to persist the data.
    # Example: await container.upsert_item({...})
    logger.info(f"Persisting to CosmosDB: {request_id}, {openai_response}")
    pass

@app.post("/consumer", summary="Consume event from Event Hub and process")
async def consume_event():
    """Consumes an event from Event Hub, checks metric, calls OpenAI, persists response, and marks event as processed."""
    request_id = str(uuid.uuid4())
    consumer_client = EventHubConsumerClient.from_connection_string(
        settings.EVENTHUB_CONNECTION_STR,
        consumer_group="$Default",
        eventhub_name=settings.EVENTHUB_NAME,
        checkpoint_store=checkpoint_store
    )
    processed_count = 0
    async def on_event(partition_context, event: EventData):
        nonlocal processed_count
        try:
            logger.info(f"Received event: {event}")
            payload = event.body_as_str(encoding="UTF-8")
            payload = json.loads(payload)
            
            messages = payload.get("messages")
            if not messages:
                 logger.warning("No 'messages' in event payload")
                 return
            utilization = await get_openai_utilization()
            if utilization < settings.METRIC_THRESHOLD:
                openai_response = await call_openai_api(messages)
                await persist_to_cosmos(payload.get("request_id", request_id), openai_response)
                await partition_context.update_checkpoint(event)
                processed_count += 1
                logger.info(f"Event processed and checkpointed. Request ID: {payload.get('request_id', request_id)}")
            else:
                logger.info(f"Utilization {utilization} >= threshold {settings.METRIC_THRESHOLD}. Event not processed.")
        except Exception as ex:
            logger.error(f"Error processing event: {ex}")
    # Receive a single event for demo (in production, use a background worker)
    await consumer_client.receive(
        on_event=on_event
    )
    await consumer_client.close()
    return {"request_id": request_id, "processed": processed_count}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8082,
        reload=True
    )
