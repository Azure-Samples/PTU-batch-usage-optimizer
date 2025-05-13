#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/variables.sh"

# Build the docker image
docker build --platform=linux/amd64 \
  -t $docImageName:$tag \
  -f "$SCRIPT_DIR/../Dockerfile" \
  --build-arg FILENAME=$docAppFile \
  --build-arg PORT=$port \
  "$SCRIPT_DIR/.."