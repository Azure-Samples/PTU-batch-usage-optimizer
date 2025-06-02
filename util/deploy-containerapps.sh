#!/usr/bin/env bash
set -euo pipefail

# resolve script dir & load shared vars
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/variables.sh"

CONSUMER_APP="${consumerAppName}"
PRODUCER_APP="${producerAppName}"
RG="${acrResourceGroupName}"

# normalize ACR name
ACR_LOWER=$(echo "$acrName" | tr '[:upper:]' '[:lower:]')

echo "Logging in to ACR: $acrName"
az acr login --name "$ACR_LOWER" --resource-group "$acrResourceGroupName"

echo "Retrieving ACR login server & creds…"
LOGIN_SERVER=$(az acr show \
  --name "$ACR_LOWER" \
  --resource-group "$acrResourceGroupName" \
  --query loginServer -o tsv)
ACR_USER=$(az acr credential show \
  --name "$ACR_LOWER" \
  --resource-group "$acrResourceGroupName" \
  --query username -o tsv)
ACR_PASS=$(az acr credential show \
  --name "$ACR_LOWER" \
  --resource-group "$acrResourceGroupName" \
  --query "passwords[0].value" -o tsv)

# Set the ACR credentials for the Container App - Consumer
echo "Setting ACR for Container App → $CONSUMER_APP"
az containerapp registry set -n "$CONSUMER_APP" \
  -g "$RG" \
  --server "$LOGIN_SERVER" \
  --username "$ACR_USER" \
  --password "$ACR_PASS"

echo "Setting ACR for Container App → $PRODUCER_APP"
az containerapp registry set -n "$PRODUCER_APP" \
  -g "$RG" \
  --server "$LOGIN_SERVER" \
  --username "$ACR_USER" \
  --password "$ACR_PASS"

echo "Updating Container App → $CONSUMER_APP"
az containerapp update \
  --container-name "$CONSUMER_APP" \
  --name "$CONSUMER_APP" \
  --resource-group "$RG" \
  --image "$LOGIN_SERVER/$consumerImageName:$tag" 

echo "Updating Container App → $PRODUCER_APP"
az containerapp update \
  --container-name "$PRODUCER_APP" \
  --name "$PRODUCER_APP" \
  --resource-group "$RG" \
  --image "$LOGIN_SERVER/$apiImageName:$tag"

echo "Done 🎉"