import logging
import uuid 

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from app.producer import Producer
from app.config import settings
from app.schemas import EventPayload, BatchEventPayload
from contextlib import asynccontextmanager
from typing import Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
async def send_event(payload: Union[EventPayload, BatchEventPayload]):
    """Receives a JSON payload or batch and sends events to Azure Event Hub"""
    request_id = str(uuid.uuid4()) 
    try:
        # normalize to a list of EventPayload
        events = (
            payload.root     # type: ignore[attr-defined]
            if isinstance(payload, BatchEventPayload)
            else [payload]
        )

        # send each payload in its own batch
        for evt in events:
            await producer.send_event(evt.messages)
        return {"request_id": request_id,
                "detail": f"{len(events)} event(s) sent successfully"}
    except ValueError as ve:
        logger.warning(f"Validation error when sending event: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as ex:
        logger.error(f"Error sending event: {ex}")
        raise HTTPException(status_code=500, detail="Failed to send event")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8082,
        reload=True
    )
