#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/variables.sh"

# Usage: ./push-docker-image.sh [api|consumer]
TARGET=${1:-api}

if [[ "$TARGET" == "api" ]]; then
  IMAGE_NAME=$apiImageName
elif [[ "$TARGET" == "consumer" ]]; then
  IMAGE_NAME=$consumerImageName
else
  echo "Unknown target: $TARGET. Use 'api' or 'consumer'."
  exit 1
fi

# Login to ACR
echo "Logging in to [$acrName] container registry..."
az acr login --name "$(echo "$acrName" | tr '[:upper:]' '[:lower:]')"

# Retrieve ACR login server
echo "Retrieving login server for the [$acrName] container registry..."
loginServer=$(az acr show --name "$(echo "$acrName" | tr '[:upper:]' '[:lower:]')" --query loginServer --output tsv)

# Push the local docker images to the Azure Container Registry
echo "Pushing the local docker images to the [$acrName] container registry..."
docker tag "$IMAGE_NAME:$tag" "$loginServer/$IMAGE_NAME:$tag"
docker push "$loginServer/$IMAGE_NAME:$tag"