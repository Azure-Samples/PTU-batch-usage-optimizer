# 🚀 PTU Batch Usage Optimizer

An open-source FastAPI REST API for optimizing the usage of PTU (Provisioned Throughput Unit) environments. This project enables users to send Azure OpenAI processes to be executed only when the PTU environment is under optimal usage conditions, maximizing efficiency and cost-effectiveness. It features native CosmosDB RBAC authentication and a flexible architecture.

> **Note:** This project is open-source and intended as a starting point. You are encouraged to adapt and extend it to fit your specific requirements and production standards.

---

## ✨ Features

- **PTU Usage Optimization**: Automatically schedules and sends Azure OpenAI processes when PTU usage is below a defined threshold
- **FastAPI**: High-performance, easy-to-use Python web framework
- **Azure Event Hub Integration**: Seamlessly dispatches events for processing
- **CosmosDB Native RBAC**: Secure authentication using Azure Entra ID (formerly AAD)
- **Structured Logging**: Consistent, production-grade logs
- **Docker Support**: Ready-to-use Dockerfiles and Compose for local and cloud deployments
- **Extensible Architecture**: Modular codebase for easy feature expansion
- **Comprehensive Testing**: Example tests included

---

## 🏁 Quickstart

### 1. Clone the Repository
```bash
git clone <repo-url>
cd PTU-batch-usage-optimizer
```

### 2. Set Up Python Environment
```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy the example file and edit your secrets:
```bash
cp .env.example .env
# Edit .env with your Azure Event Hub, CosmosDB, and PTU settings
```

### 5. Run the API
```bash
uvicorn main:app --reload
```

---

## 🧑‍💻 API Endpoints

### Health Check
- `GET /health`  
  _Returns API health status._

### Send Event
- `POST /events`  
  _Send a JSON event to Azure Event Hub for PTU-optimized processing._

**Request Example:**
```json
{
  "data": {
    "openai_process": {
      "prompt": "...",
      "parameters": { "max_tokens": 100 }
    },
    "ptu_condition": {
      "max_utilization": 0.7
    }
  }
}
```

**Response Example:**
```json
{
  "detail": "Event sent successfully and will be processed when PTU usage is optimal."
}
```

---

## ⚡ How It Works

- The API receives requests to process Azure OpenAI jobs.
- It checks the current PTU environment usage (via Azure Monitor).
- If the usage is below the configured threshold (for example, 70% PTU-M usage), the job is dispatched immediately.
- If not, the job is queued and dispatched when conditions are optimal.
- All events and job states are tracked in CosmosDB for reliability, auditing and be able to consume the processed responses.

---

## 🔐 CosmosDB Entra ID (RBAC) Permissions

This project uses [CosmosDB native RBAC](https://aka.ms/cosmos-native-rbac) for secure authentication. To grant permissions:

1. **Login to Azure:**
   ```bash
   az login
   ```
2. **Allow Key Authentication on CosmosDB:**
   ```bash
   resourceGroupName=<your-resource-group-name>
   accountName=<your-cosmosdb-account-name>

   az resource update --resource-type "Microsoft.DocumentDB/databaseAccounts" \
     --resource-group $resourceGroupName \
     --name $accountName \
     --set properties.disableLocalAuth=false
   ```
3. **Assign RBAC Role:**
   - Go to the [Azure Portal](https://portal.azure.com/)
   - Navigate to your CosmosDB account
   - Assign the appropriate role (e.g., `Cosmos DB Built-in Data Contributor`) to your user or service principal

---

## ⚙️ Environment Variables

| Variable                | Description                                 |
|-------------------------|---------------------------------------------|
| `EVENTHUB_CONNECTION_STR` | Azure Event Hub namespace connection string |
| `EVENTHUB_NAME`           | Name of the target Event Hub                |
| `COSMOSDB_URI`            | CosmosDB account URI                        |
| `COSMOSDB_DATABASE`       | CosmosDB database name                      |
| `COSMOSDB_CONTAINER`      | CosmosDB container name                     |
| `AZURE_CLIENT_ID`         | Azure Entra ID client ID                    |
| `AZURE_TENANT_ID`         | Azure Entra ID tenant ID                    |
| `AZURE_CLIENT_SECRET`     | Azure Entra ID client secret                |
| `PTU_MAX_UTILIZATION`     | Max allowed PTU utilization (e.g., 0.7)     |

---

## 🐳 Docker & Deployment

- **Build API Docker Image Locally:**
  ```bash
  ./util/build-docker-image.sh api
  ```
- **Build Consumer Docker Image Locally:**
  ```bash
  ./util/build-docker-image.sh consumer
  ```
- **Push API Docker Image to ACR:**
  ```bash
  ./util/push-docker-image.sh api
  ```
- **Push Consumer Docker Image to ACR:**
  ```bash
  ./util/push-docker-image.sh consumer
  ```
- **Run with Docker Compose:**
  ```bash
  docker-compose up --build
  ```

### 🚀 Build & Push to Azure Container Registry (ACR) using provided scripts

1. **Configure your variables:**
   - Edit `util/variables.sh` with your ACR name, image names, and tag.
2. **Login to Azure:**
   ```bash
   az login
   ```
3. **Build the Docker images:**
   ```bash
   ./util/build-docker-image.sh api
   ./util/build-docker-image.sh consumer
   ```
4. **Push the images to ACR:**
   ```bash
   ./util/push-docker-image.sh api
   ./util/push-docker-image.sh consumer
   ```

These scripts will automatically tag and push your images to the Azure Container Registry as configured in your `variables.sh` file.

---

## 📁 Project Structure

```
PTU-batch-usage-optimizer/
├── app/                # Core application code
│   ├── config.py       # Configuration management
│   ├── schemas.py      # Pydantic schemas
│   └── ...
├── src/                # EventHub, Cosmos, PTU monitoring, and processing logic
├── main.py             # FastAPI entrypoint
├── consumer_service.py # Consumer service
├── requirements.txt    # Python dependencies
├── Dockerfile*         # Docker configurations
├── util/               # Utility scripts
└── tests/              # Test suite
```

---

## 📚 Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Azure Event Hub Docs](https://docs.microsoft.com/azure/event-hubs/)
- [CosmosDB RBAC](https://aka.ms/cosmos-native-rbac)
- [Azure OpenAI Service](https://learn.microsoft.com/azure/ai-services/openai/)
- [Provisioned Throughput Units (PTU)](https://learn.microsoft.com/azure/cosmos-db/provision-throughput)

---

## 📝 License

MIT License. See [LICENSE](LICENSE) for details.
