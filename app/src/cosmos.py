import logging
from azure.cosmos.aio import CosmosClient
from azure.cosmos.exceptions import CosmosResourceExistsError
from ..config import settings

logger = logging.getLogger(__name__)


class CosmosDBClient:
    def __init__(self):
        self.endpoint = settings.COSMOSDB_ENDPOINT
        self.key = settings.COSMOSDB_KEY
        self.database_name = settings.COSMOSDB_DATABASE
        self.container_name = settings.COSMOSDB_CONTAINER

    async def persist_response(self, request_id, openai_response):
        """
        Persists the OpenAI response and request_id into Azure CosmosDB.
        """
        try:
            async with CosmosClient(self.endpoint, self.key) as client:
                db = client.get_database_client(self.database_name)
                container = db.get_container_client(self.container_name)
                document = {
                    "id": request_id,
                    "openai_response": openai_response
                }
                await container.create_item(document)
                logger.info(f"Persisted document to CosmosDB: {request_id}")
        except CosmosResourceExistsError:
            logger.warning(f"Document with id {request_id} already exists in CosmosDB.")
        except Exception as ex:
            logger.error(f"Failed to persist to CosmosDB: {ex}")
            raise
