#!/bin/bash

CONTAINER_NAME="discord-bot"
IMAGE_NAME="afc-discord-bot"
PORT=10000

if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    exit 1
fi

echo "Stopping and removing existing container..."
docker stop $CONTAINER_NAME
docker rm $CONTAINER_NAME

echo "Building the Docker image..."
docker build --no-cache -t $IMAGE_NAME .

echo "Running the Docker container..."
docker run -d \
    --name $CONTAINER_NAME \
    --env-file .env \
    -p $PORT:$PORT \
    $IMAGE_NAME

echo "📜 Streaming logs..."
docker logs -f $CONTAINER_NAME