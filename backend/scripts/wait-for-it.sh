#!/usr/bin/env bash
#
# wait-for-it.sh — Wait for a service (HOST:PORT) to become available, then run a command.

set -Eeuo pipefail  # safer bash scripting (abort on errors, etc.)

# Default configurations
TIMEOUT=15
STRICT=0
DEBUG=0

# Logging functions
log_debug() {
  [[ "$DEBUG" == "1" ]] && echo "[DEBUG] $*"
}

log_info() {
  echo "[INFO] $*"
}

log_error() {
  echo "[ERROR] $*" >&2
}

# Usage/help message
usage() {
  cat <<EOF
Usage: $(basename "$0") [options] host:port [-- command args...]
Options:
  --timeout=NUM   Set timeout in seconds (default: 15)
  --strict        Exit with an error if the host:port is not reachable
  --debug         Enable debug output
Example:
  $(basename "$0") --timeout=30 --strict example.com:80 -- echo "Service is up!"
EOF
}

# Parse arguments
HOST_PORT=""
COMMAND=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --timeout=*)
      TIMEOUT="${1#*=}"
      ;;
    --strict)
      STRICT=1
      ;;
    --debug)
      DEBUG=1
      ;;
    --)
      shift
      COMMAND="$*"
      break
      ;;
    -*)
      log_error "Unknown option: $1"
      usage
      exit 1
      ;;
    *)
      if [[ -z "$HOST_PORT" ]]; then
        HOST_PORT="$1"
      else
        log_error "Unexpected extra argument: $1"
        usage
        exit 1
      fi
      ;;
  esac
  shift
done

# Validate host:port
if [[ -z "$HOST_PORT" ]]; then
  log_error "Missing host:port argument."
  usage
  exit 1
fi

if [[ "$HOST_PORT" != *:* ]]; then
  log_error "Invalid host:port format: $HOST_PORT"
  exit 1
fi

HOST="${HOST_PORT%:*}"
PORT="${HOST_PORT#*:}"

log_debug "Timeout: $TIMEOUT, Strict: $STRICT, Debug: $DEBUG"
log_info "Waiting for $HOST:$PORT to become available..."

# Wait for the service
START_TIME=$(date +%s)

while true; do
  if nc -z "$HOST" "$PORT" >/dev/null 2>&1; then
    log_info "$HOST:$PORT is available!"
    break
  fi

  CURRENT_TIME=$(date +%s)
  ELAPSED_TIME=$((CURRENT_TIME - START_TIME))

  if (( ELAPSED_TIME >= TIMEOUT )); then
    log_error "Timeout reached after $TIMEOUT seconds trying to connect to $HOST:$PORT."
    if (( STRICT )); then
      exit 1
    else
      break
    fi
  fi

  sleep 1
done

# Execute the command if provided
if [[ -n "$COMMAND" ]]; then
  log_info "Executing command: $COMMAND"
  exec $COMMAND
else
  exit 0
fi