import json
import logging
from azure.eventhub.aio import EventHubConsumerClient
from azure.eventhub import EventData
from azure.eventhub.extensions.checkpointstoreblobaio import BlobCheckpointStore
from azure.cosmos.aio import CosmosClient
from ..config import settings
from app.src.azure_openai import AzureOpenAI

logger = logging.getLogger(__name__)

class Consumer:
    def __init__(self, checkpoint_store=None):
        self.checkpoint_store = checkpoint_store or BlobCheckpointStore.from_connection_string(
            settings.STORAGE_ACCOUNT_CHECKPOINT_STORE,
            settings.STORAGE_ACCOUNT_CHECKPOINT_STORE_CONTAINER
        )
        self.consumer_client = EventHubConsumerClient.from_connection_string(
            settings.EVENTHUB_CONNECTION_STR,
            consumer_group="$Default",
            eventhub_name=settings.EVENTHUB_NAME,
            checkpoint_store=self.checkpoint_store
        )
        self.azure_openai = AzureOpenAI()

    async def get_openai_utilization(self):
        return 0.3

    async def persist_to_cosmos(self, request_id, openai_response):
        logger.info(f"Persisting to CosmosDB: {request_id}, {openai_response}")
        pass

    async def consume_event(self):
        processed_count = 0
        async def on_event(partition_context, event: EventData):
            nonlocal processed_count
            try:
                logger.info(f"Received event: {event}")
                payload = event.body_as_str(encoding="UTF-8")
                payload = json.loads(payload)
                messages = payload.get("messages")

                # get the remaining payload content (expect messages and request_id)
                content = {k: v for k, v in payload.items() if k not in ["messages", "request_id"]}

                logger.info(f"Payload content: {content}")
                logger.info(f"Messages: {messages}")

                # Consolidate the azure openai API call as a JSON object
                aoai_payload = {
                    "messages": messages,
                    **content
                }

                if not messages:
                    logger.warning("No 'messages' in event payload")
                    return
                utilization = await self.get_openai_utilization()
                if utilization < settings.METRIC_THRESHOLD:
                    openai_response = await self.azure_openai.send_llm_request(aoai_payload)
                    await self.persist_to_cosmos(payload.get("request_id"), openai_response)
                    await partition_context.update_checkpoint(event)
                    processed_count += 1
                    logger.info(f"Event processed and checkpointed. Request ID: {payload.get('request_id')}")
                else:
                    logger.info(f"Utilization {utilization} >= threshold {settings.METRIC_THRESHOLD}. Event not processed.")
            except Exception as ex:
                logger.error(f"Error processing event: {ex}")
        await self.consumer_client.receive(on_event=on_event)
        await self.consumer_client.close()
        return processed_count
