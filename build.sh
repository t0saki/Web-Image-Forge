#!/bin/bash

# Set image name and tag
IMAGE_NAME="image-optimizer"
IMAGE_TAG="latest"

# Full image reference
FULL_IMAGE="${IMAGE_NAME}:${IMAGE_TAG}"

echo "Building Docker image: ${FULL_IMAGE}"
docker build -t ${FULL_IMAGE} .

echo "Image built successfully!"
echo "To use this image in docker-compose, make sure your docker-compose.yml references: ${FULL_IMAGE}" 