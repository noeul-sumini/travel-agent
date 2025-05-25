#!/bin/bash

# Exit on error
set -e

# Load environment variables
if [ -f .env.${ENV:-dev} ]; then
    export $(cat .env.${ENV:-dev} | grep -v '^#' | xargs)
fi



# Set environment
export ENV=${ENV:-dev}

# Start services using docker-compose
echo "Starting services with docker-compose..."
sudo docker-compose up --build

echo "Deployment completed successfully!"
echo "Backend is running on http://localhost:8000"
echo "Frontend is running on http://localhost:8501"