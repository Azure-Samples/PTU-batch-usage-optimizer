# Azure Event Hub API

A FastAPI-based REST API to send events to Azure Event Hub.

## Features

- FastAPI for building the REST API
- Pydantic for request validation
- Azure Event Hub Producer Client for sending events
- Environment-based configuration with `python-dotenv`
- Structured logging and global error handling

## Prerequisites

- Python 3.8+
- Azure Event Hub namespace and event hub created

## Setup

1. Clone this repository:
   ```bash
   git clone <repo-url>
   cd PTU-batch-usage-optimizer
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and set your Azure Event Hub values:
   ```bash
   cp .env.example .env
   ```

5. Run the API:
   ```bash
   uvicorn main:app --reload
   ```

## API Endpoints

- `GET /health` - Health check
- `POST /events` - Send an event to Azure Event Hub

### Send Event

Request:
```http
POST /events HTTP/1.1
Content-Type: application/json

{
  "data": {
    "key1": "value1",
    "key2": 123
  }
}
```

Response:
```http
HTTP/1.1 201 Created
Content-Type: application/json

{ "detail": "Event sent successfully" }
```

## CosmosDB EntraID permissions
We use the [CosmosDB native RBAC](https://aka.ms/cosmos-native-rbac) to authenticate with the application. Follow the instructions below to give the permission to the user/service-principal:

1. `az login`
2. Allow Key authentication on Azure CosmosDB

```bash
resourceGroupName=<your-resource-group-name>
accountName=<your-cosmosdb-account-name>

az resource update --resource-type "Microsoft.DocumentDB/databaseAccounts" --resource-group $resourceGroupName --name $accountName --set properties.disableLocalAuth=false
```

## Environment Variables

- `EVENTHUB_CONNECTION_STR` - Connection string for the Azure Event Hub namespace
- `EVENTHUB_NAME` - Name of the target event hub

## License

MIT License
