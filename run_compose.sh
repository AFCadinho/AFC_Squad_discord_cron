#!/bin/bash

echo "Stopping and removing existing containers (if any)..."
docker compose down

echo "Building and starting containers..."
docker compose up --build -d

echo "Containers are up and running."
