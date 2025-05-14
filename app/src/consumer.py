import json
import logging
from azure.eventhub.aio import EventHubConsumerClient
from azure.eventhub import EventData
from azure.eventhub.extensions.checkpointstoreblobaio import BlobCheckpointStore
from ..config import settings
from app.src.azure_openai import AzureOpenAI
from app.src.cosmos import CosmosDBClient
from app.src.monitor import AzureMonitorClient

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
        self.azure_openai_client = AzureOpenAI()
        self.cosmos_client = CosmosDBClient()
        self.monitor_client = AzureMonitorClient()

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

                # Check the PTU Deployment usage
                utilization = await self.monitor_client.get_latest_utilization()

                if utilization < settings.METRIC_THRESHOLD:
                    # Call the Azure OpenAI API
                    openai_response = await self.azure_openai_client.send_llm_request(aoai_payload)

                    # Persist the OpenAI response to CosmosDB
                    await self.cosmos_client.persist_response(payload.get("request_id"), 
                                                              openai_response)

                    # Checkpoint the event
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