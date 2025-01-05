#!/bin/bash

# Start up script with detailed logging for Docker Compose services

LOG_FILE="startup.log"

echo "Starting services at $(date)" | tee -a $LOG_FILE

# Check Docker is running
if ! docker info >/dev/null 2>&1; then
  echo "Docker is not running. Please start Docker and try again." | tee -a $LOG_FILE
  exit 1
fi

# Start Docker Compose
echo "Starting Docker Compose..." | tee -a $LOG_FILE
docker compose up -d | tee -a $LOG_FILE

# Wait for services to start
echo "Waiting for services to start..." | tee -a $LOG_FILE
sleep 10

# Log the status of each service
services=("db" "backend" "frontend")

for service in "${services[@]}"; do
  echo "Checking status for $service..." | tee -a $LOG_FILE
  STATUS=$(docker inspect -f '{{.State.Status}}' "$service" 2>/dev/null)
  
  if [[ "$STATUS" == "running" ]]; then
    echo "$service is running." | tee -a $LOG_FILE
  else
    echo "$service failed to start or is not running. Status: $STATUS" | tee -a $LOG_FILE
  fi
done

# Check health of database service
echo "Checking health of database service..." | tee -a $LOG_FILE
DB_HEALTH=$(docker inspect --format='{{json .State.Health.Status}}' db 2>/dev/null)

if [[ "$DB_HEALTH" == "\"healthy\"" ]]; then
  echo "Database service is healthy." | tee -a $LOG_FILE
else
  echo "Database service is not healthy. Current health status: $DB_HEALTH" | tee -a $LOG_FILE
fi

echo "Services started at $(date)" | tee -a $LOG_FILE
echo "Startup script completed." | tee -a $LOG_FILE