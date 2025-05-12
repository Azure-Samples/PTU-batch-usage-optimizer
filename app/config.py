import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Azure Event Hub settings
    EVENTHUB_CONNECTION_STR = os.getenv('EVENTHUB_CONNECTION_STR')
    EVENTHUB_NAME = os.getenv('EVENTHUB_NAME')
    STORAGE_ACCOUNT_CHECKPOINT_STORE = os.getenv('STORAGE_ACCOUNT_CHECKPOINT_STORE')
    STORAGE_ACCOUNT_CHECKPOINT_STORE_CONTAINER = os.getenv('STORAGE_ACCOUNT_CHECKPOINT_STORE_CONTAINER')

    # Azure Monitor/OpenAI/CosmosDB settings
    OPENAI_RESOURCE_ID = os.getenv('OPENAI_RESOURCE_ID')
    METRIC_THRESHOLD = float(os.getenv('METRIC_THRESHOLD', '0.7'))
    COSMOSDB_ENDPOINT = os.getenv('COSMOSDB_ENDPOINT')
    COSMOSDB_KEY = os.getenv('COSMOSDB_KEY')
    COSMOSDB_DATABASE = os.getenv('COSMOSDB_DATABASE')
    COSMOSDB_CONTAINER = os.getenv('COSMOSDB_CONTAINER')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_API_URL = os.getenv('OPENAI_API_URL')

settings = Settings()
