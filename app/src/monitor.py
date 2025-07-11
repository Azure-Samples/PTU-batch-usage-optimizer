from datetime import timedelta
from azure.identity.aio import DefaultAzureCredential
from azure.monitor.query.aio import MetricsQueryClient
from azure.monitor.query import MetricAggregationType
from app.config import settings


class AzureMonitorClient:
    def __init__(self):
        self.resource_id = settings.AZURE_OPENAI_RESOURCE_ID
        self.metric_name = "AzureOpenAIProvisionedManagedUtilizationV2"

        # If settings.AZURE_CLIENT_ID is not set, use DefaultAzureCredential for local development
        self.credential = DefaultAzureCredential() if settings.AZURE_CLIENT_ID is None else DefaultAzureCredential(managed_identity_client_id=settings.AZURE_CLIENT_ID)

    async def get_latest_utilization(self):
        if not self.resource_id:
            raise ValueError("OPENAI_RESOURCE_ID is not set in environment variables")
        async with MetricsQueryClient(self.credential) as client:
            response = await client.query_resource(
                self.resource_id,
                metric_names=[self.metric_name],
                aggregations=[MetricAggregationType.AVERAGE],
                timespan=timedelta(minutes=1),
                granularity=timedelta(minutes=1),
            )
            for metric in response.metrics:
                for timeseries_element in metric.timeseries:
                    if timeseries_element.data:
                        # Get the latest data point
                        latest = timeseries_element.data[-1]
                        return latest.average
        # If no data is available, return 0.0
        return 0.0
