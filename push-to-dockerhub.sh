#!/bin/bash
# Script to build and push Docker image to Docker Hub

set -e  # Exit on error

DOCKER_USERNAME="dmitryodinoky"
IMAGE_NAME="telegram-bot-sdxl"
TAG="latest"

echo "======================================"
echo "Building Docker Image for Coolify"
echo "======================================"

# Build the image
echo "Building image..."
docker build -t ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG} .

# Tag with version (optional)
VERSION=$(date +%Y%m%d-%H%M%S)
docker tag ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG} ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}

echo ""
echo "======================================"
echo "Image built successfully!"
echo "======================================"
echo "Image: ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}"
echo "Version: ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}"
echo ""

# Login to Docker Hub (you'll be prompted for credentials)
echo "======================================"
echo "Logging in to Docker Hub"
echo "======================================"
echo "Please enter your Docker Hub credentials:"
docker login

echo ""
echo "======================================"
echo "Pushing to Docker Hub"
echo "======================================"

# Push the images
echo "Pushing latest tag..."
docker push ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}

echo "Pushing version tag..."
docker push ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}

echo ""
echo "======================================"
echo "✅ SUCCESS!"
echo "======================================"
echo "Image pushed to Docker Hub:"
echo "  - ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}"
echo "  - ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}"
echo ""
echo "Update your Coolify docker-compose.yml to use:"
echo "  image: ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}"
echo ""
echo "Or use docker-compose.coolify.yml which is already configured!"
echo "======================================"
