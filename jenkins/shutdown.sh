#!/bin/bash
# Shutdown script for transport application
echo "Stopping transport application..."
docker-compose -f docker-compose.yaml down
echo "Application stopped successfully"