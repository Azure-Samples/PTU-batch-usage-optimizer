import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Azure Event Hub settings
    EVENTHUB_CONNECTION_STR = os.getenv('EVENTHUB_CONNECTION_STR')
    EVENTHUB_NAME = os.getenv('EVENTHUB_NAME')

settings = Settings()
