#!/bin/bash

# Constants
MAX_RETRIES=5
RETRY_INTERVAL=10
LOG_FILE="startup.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

log_message() {
    echo "[${TIMESTAMP}] $1" | tee -a "${LOG_FILE}"
}

check_service_health() {
    local service=$1
    local retries=0
    
    while [ $retries -lt $MAX_RETRIES ]; do
        case $service in
            "db")
                if docker exec postgres_db pg_isready -U macmini > /dev/null 2>&1; then
                    log_message "Database is healthy"
                    return 0
                fi
                ;;
            "backend")
                if curl -s http://localhost:8000/health > /dev/null; then
                    log_message "Backend service is healthy"
                    return 0
                fi
                ;;
            "frontend")
                if curl -s http://localhost:3000 > /dev/null; then
                    log_message "Frontend service is healthy"
                    return 0
                fi
                ;;
        esac
        
        retries=$((retries + 1))
        log_message "Waiting for $service to become healthy (attempt $retries/$MAX_RETRIES)"
        sleep $RETRY_INTERVAL
    done
    
    log_message "ERROR: $service failed to become healthy after $MAX_RETRIES attempts"
    return 1
}

cleanup() {
    log_message "Cleaning up services..."
    docker compose down
}

# Main script
log_message "Starting services..."

# Start services
if ! docker compose up -d; then
    log_message "ERROR: Failed to start services"
    cleanup
    exit 1
fi

# Check health of each service
for service in db backend frontend; do
    log_message "Checking health of $service..."
    if ! check_service_health $service; then
        log_message "ERROR: Service $service failed health check"
        cleanup
        exit 1
    fi
done

log_message "All services started successfully"