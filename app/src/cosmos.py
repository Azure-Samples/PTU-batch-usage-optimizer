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

    async def get_response_by_request_id(self, request_id):
        """
        Fetches the OpenAI response from CosmosDB by request_id.
        Returns the document if found, otherwise None.
        """
        try:
            async with CosmosClient(self.endpoint, self.key) as client:
                db = client.get_database_client(self.database_name)
                container = db.get_container_client(self.container_name)
                response = await container.read_item(item=request_id, partition_key=request_id)
                return response
        except Exception as ex:
            if "Resource Not Found" in str(ex) or "NotFound" in str(ex):
                logger.info(f"No document found in CosmosDB for request_id: {request_id}")
                return None
            logger.error(f"Error fetching document from CosmosDB: {ex}")
            raise
