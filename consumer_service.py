import logging
from app.src.consumer import Consumer
from app.config import settings
from azure.eventhub.extensions.checkpointstoreblobaio import BlobCheckpointStore
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

checkpoint_store = BlobCheckpointStore.from_connection_string(
    settings.STORAGE_ACCOUNT_CHECKPOINT_STORE,
    settings.STORAGE_ACCOUNT_CHECKPOINT_STORE_CONTAINER
)

async def main():
    consumer = Consumer(checkpoint_store=checkpoint_store)
    logger.info("Consumer initialized. Starting event consumption loop...")
    while True:
        processed_count = await consumer.consume_event()
        logger.info(f"Events processed in this cycle: {processed_count}")
        await asyncio.sleep(1)  # Adjust sleep as needed

if __name__ == "__main__":
    asyncio.run(main())
