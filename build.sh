#!/bin/bash

# Set image name and tag
IMAGE_NAME="tosakiup/image-optimizer"
IMAGE_TAG="latest"

# Full image reference
FULL_IMAGE="${IMAGE_NAME}:${IMAGE_TAG}"

echo "Building Docker image: ${FULL_IMAGE}"
docker build -t ${FULL_IMAGE} .

echo "Image built successfully!"

docker push ${FULL_IMAGE}

echo "Image pushed successfully!"