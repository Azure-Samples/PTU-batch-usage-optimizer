#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/variables.sh"

# Usage: ./build-docker-image.sh [api|consumer]
TARGET=${1:-api}

if [[ "$TARGET" == "api" ]]; then
  IMAGE_NAME=$apiImageName
  DOCKERFILE="$SCRIPT_DIR/../Dockerfile.api"
elif [[ "$TARGET" == "consumer" ]]; then
  IMAGE_NAME=$consumerImageName
  DOCKERFILE="$SCRIPT_DIR/../Dockerfile.consumer"
else
  echo "Unknown target: $TARGET. Use 'api' or 'consumer'."
  exit 1
fi

docker build --platform=linux/amd64 \
  -t $IMAGE_NAME:$tag \
  -f "$DOCKERFILE" \
  "$SCRIPT_DIR/.."