#!/bin/bash

CONTAINER_NAME="cws-cronjob"
IMAGE_NAME="webhook-cron"

# Remove existing container if it exists
if [ "$(docker ps -aq -f name=^/${CONTAINER_NAME}$)" ]; then
    echo "Removing existing container: $CONTAINER_NAME"
    docker rm -f $CONTAINER_NAME
fi

# Build the Docker image
echo "Building Docker image: $IMAGE_NAME"
docker build -t $IMAGE_NAME .

# Run the container
echo "Running container: $CONTAINER_NAME"
docker run -d --name $CONTAINER_NAME $IMAGE_NAME
