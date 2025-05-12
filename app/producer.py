import json
from azure.eventhub.aio import EventHubProducerClient
from azure.eventhub import EventData
from .config import settings
import logging

logger = logging.getLogger(__name__)

class Producer:
    def __init__(self):
        if not settings.EVENTHUB_CONNECTION_STR or not settings.EVENTHUB_NAME:
            logger.error("Event Hub connection string or name not set in environment variables")
            raise ValueError("Missing Event Hub configuration")
        # Initialize async Event Hub producer client
        self.client = EventHubProducerClient.from_connection_string(
            conn_str=settings.EVENTHUB_CONNECTION_STR,
            eventhub_name=settings.EVENTHUB_NAME
        )

    async def send_event(self, payload: dict):
        """Create a batch and send event data asynchronously"""
        # Create a batch
        event_data_batch = await self.client.create_batch()
        # Add event data
        event_data_batch.add(EventData(json.dumps(payload)))
        # Send batch within async context
        async with self.client:
            await self.client.send_batch(event_data_batch)
        logger.info("Event sent to Azure Event Hub")

    async def close(self):
        """Close the Event Hub client connection"""
        await self.client.close()
