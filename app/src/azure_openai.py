import os, requests


class AzureOpenAI():
    def __init__(self):
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment_name = os.getenv("AZURE_OPENAI_PTU_DEPLOYMENT_NAME")

    async def send_llm_request(self, 
                               payload):
        if not self.api_key or not self.endpoint or not self.deployment_name:
            raise ValueError("API key, endpoint, or model not found in environment variables")

        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }
     
        response = requests.post(f"{self.endpoint}/openai/deployments/{self.deployment_name}/chat/completions?api-version=2025-04-01-preview", 
                                 headers=headers, 
                                 json=payload)

        if response.status_code == 429:
            raise requests.exceptions.RequestException(f"Request failed with status code 429: {response.text}")
        elif response.status_code != 200:
            raise Exception(f"Request failed with status code {response.status_code}: {response.text}")

        return response.json()