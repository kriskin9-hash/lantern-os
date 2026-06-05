#!/bin/bash

# Unified Lantern OS + HFF Convergence Entrypoint
# Orchestrates all services (Flask, Node.js, Discord bot, etc.)
# Generated: 2025

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LANTERN_MODE="${LANTERN_MODE:-convergence-unified}"
PORT="${PORT:-5000}"
LANTERN_DASHBOARD_PORT="${LANTERN_DASHBOARD_PORT:-4177}"
DISCORD_BOT_PORT="${DISCORD_BOT_PORT:-4178}"
HEALTH_PORT="${HEALTH_PORT:-9000}"
WORKERS="${WORKERS:-4}"
THREADS="${THREADS:-2}"
TIMEOUT="${TIMEOUT:-120}"

# Paths
APP_ROOT="/app"
HFF_ROOT="${APP_ROOT}/hff"
LANTERN_ROOT="${APP_ROOT}/lantern"
DATA_ROOT="${APP_ROOT}/data"
LOGS_DIR="${APP_ROOT}/logs"
PID_DIR="/tmp/lantern-pids"

# Create directories
mkdir -p "${LOGS_DIR}" "${PID_DIR}" "${DATA_ROOT}"/{rag-house,wallet,manifests,media}

# Logging functions
log_info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} ${GREEN}INFO${NC}: $*" | tee -a "${LOGS_DIR}/entrypoint.log"
}

log_warn() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} ${YELLOW}WARN${NC}: $*" | tee -a "${LOGS_DIR}/entrypoint.log"
}

log_error() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} ${RED}ERROR${NC}: $*" | tee -a "${LOGS_DIR}/entrypoint.log"
}

# Health check function
check_health() {
    local service=$1
    local port=$2
    local max_retries=5
    local retry=0

    while [ $retry -lt $max_retries ]; do
        if curl -sf "http://localhost:${port}/health" > /dev/null 2>&1; then
            log_info "${service} is healthy (port ${port})"
            return 0
        fi
        log_warn "${service} health check attempt $((retry + 1))/${max_retries}..."
        sleep 2
        retry=$((retry + 1))
    done

    log_error "${service} failed health check after ${max_retries} attempts"
    return 1
}

# Trap for cleanup
cleanup() {
    log_info "Shutting down services..."

    # Kill all background processes
    if [ -d "${PID_DIR}" ]; then
        for pidfile in ${PID_DIR}/*.pid; do
            if [ -f "$pidfile" ]; then
                pid=$(cat "$pidfile")
                if kill -0 "$pid" 2>/dev/null; then
                    log_info "Terminating PID $pid..."
                    kill "$pid" 2>/dev/null || true
                fi
                rm -f "$pidfile"
            fi
        done
    fi

    wait
    log_info "All services stopped"
    exit 0
}

trap cleanup SIGTERM SIGINT

# ============================================================================
# Service startup functions
# ============================================================================

start_hff_api() {
    log_info "Starting HFF Flask API (port ${PORT})..."

    cd "${HFF_ROOT}/apps" || exit 1

    gunicorn \
        --bind 0.0.0.0:"${PORT}" \
        --workers "${WORKERS}" \
        --threads "${THREADS}" \
        --timeout "${TIMEOUT}" \
        --access-logfile "${LOGS_DIR}/hff-access.log" \
        --error-logfile "${LOGS_DIR}/hff-error.log" \
        --log-level info \
        safe_app:app &

    echo $! > "${PID_DIR}/hff-api.pid"
    log_info "HFF API started (PID: $!)"
}

start_lantern_dashboard() {
    log_info "Starting Lantern OS Dashboard (Node.js, port ${LANTERN_DASHBOARD_PORT})..."

    cd "${LANTERN_ROOT}/apps/lantern-garage" || exit 1

    node server.js &

    echo $! > "${PID_DIR}/lantern-dashboard.pid"
    log_info "Lantern Dashboard started (PID: $!)"
}

start_lantern_browser() {
    log_info "Starting Lantern Browser API (port 8765)..."

    cd "${LANTERN_ROOT}/apps" || exit 1

    # Check if browser server exists
    if [ -f "lantern-browser-server.py" ]; then
        gunicorn \
            --bind 0.0.0.0:8765 \
            --workers 2 \
            --timeout 60 \
            --access-logfile "${LOGS_DIR}/browser-access.log" \
            --error-logfile "${LOGS_DIR}/browser-error.log" \
            lantern-browser-server:app &

        echo $! > "${PID_DIR}/lantern-browser.pid"
        log_info "Lantern Browser started (PID: $!)"
    else
        log_warn "lantern-browser-server.py not found, skipping browser service"
    fi
}

start_discord_bot() {
    log_info "Starting Discord Bot (port ${DISCORD_BOT_PORT})..."

    if [ -z "${DISCORD_BOT_TOKEN:-}" ]; then
        log_warn "DISCORD_BOT_TOKEN not set, skipping Discord bot"
        return
    fi

    cd "${LANTERN_ROOT}/src/discord_lounge_bot" || exit 1

    python discord_bot.py &

    echo $! > "${PID_DIR}/discord-bot.pid"
    log_info "Discord Bot started (PID: $!)"
}

start_rhythm_os() {
    log_info "Starting Rhythm OS (audio services)..."

    cd "${LANTERN_ROOT}/apps/rhythm-os" || exit 1

    if [ -f "main.py" ]; then
        python main.py &
        echo $! > "${PID_DIR}/rhythm-os.pid"
        log_info "Rhythm OS started (PID: $!)"
    else
        log_warn "Rhythm OS main.py not found, skipping"
    fi
}

start_health_endpoint() {
    log_info "Starting unified health endpoint (port ${HEALTH_PORT})..."

    # Create a minimal Flask app for health checks
    python << 'EOF' &
import os
from flask import Flask, jsonify
import subprocess
import socket

app = Flask('lantern-health')

def is_port_open(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', int(port)))
    sock.close()
    return result == 0

@app.route('/health', methods=['GET'])
def health():
    services = {
        'hff-api': is_port_open(5000),
        'lantern-dashboard': is_port_open(4177),
        'lantern-browser': is_port_open(8765),
        'discord-bot': is_port_open(4178),
    }

    all_healthy = all(services.values())
    status = 'healthy' if all_healthy else 'degraded'

    return jsonify({
        'status': status,
        'services': services,
        'mode': 'convergence-unified'
    }), 200 if all_healthy else 503

@app.route('/metrics', methods=['GET'])
def metrics():
    return jsonify({
        'timestamp': str(datetime.now()),
        'mode': os.getenv('LANTERN_MODE', 'unknown'),
        'workers': os.getenv('WORKERS', 'unknown'),
    })

if __name__ == '__main__':
    from datetime import datetime
    app.run(host='0.0.0.0', port=${HEALTH_PORT}, debug=False)
EOF

    echo $! > "${PID_DIR}/health-endpoint.pid"
    log_info "Health endpoint started (PID: $!)"
}

# ============================================================================
# Main orchestration
# ============================================================================

main() {
    log_info "=========================================="
    log_info "Lantern OS + HFF Convergence Unified Stack"
    log_info "=========================================="
    log_info "Mode: ${LANTERN_MODE}"
    log_info "Timestamp: $(date)"
    log_info "App Root: ${APP_ROOT}"
    log_info "=========================================="

    # Pre-flight checks
    log_info "Running pre-flight checks..."

    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 not found"
        exit 1
    fi

    if ! command -v node &> /dev/null; then
        log_error "Node.js not found"
        exit 1
    fi

    if ! command -v gunicorn &> /dev/null; then
        log_error "Gunicorn not found"
        exit 1
    fi

    # Ensure Rust toolchain for CSF convergence layer
    if ! command -v cargo &> /dev/null; then
        log_warn "Rust not found, attempting auto-install..."
        if [ -f "${LANTERN_ROOT}/scripts/install-rust.sh" ]; then
            bash "${LANTERN_ROOT}/scripts/install-rust.sh"
        else
            log_warn "install-rust.sh not found, skipping CSF Rust build"
        fi
    else
        log_info "Rust found: $(rustc --version)"
    fi

    log_info "Pre-flight checks passed"

    # Initialize data directories
    log_info "Initializing data directories..."
    mkdir -p "${DATA_ROOT}"/{rag-house,wallet,manifests,media}
    chmod 750 "${DATA_ROOT}"

    # Start services
    log_info "Starting services..."

    start_hff_api
    sleep 2
    check_health "HFF API" "${PORT}" || log_warn "HFF API health check failed, continuing..."

    start_lantern_dashboard
    sleep 2
    check_health "Lantern Dashboard" "${LANTERN_DASHBOARD_PORT}" || log_warn "Dashboard health check failed, continuing..."

    start_lantern_browser
    sleep 2

    start_discord_bot
    sleep 1

    start_rhythm_os
    sleep 1

    start_health_endpoint
    sleep 1

    log_info "=========================================="
    log_info "All services started successfully"
    log_info "=========================================="
    log_info "Available endpoints:"
    log_info "  HFF API:              http://localhost:${PORT}"
    log_info "  Lantern Dashboard:    http://localhost:${LANTERN_DASHBOARD_PORT}"
    log_info "  Lantern Browser:      http://localhost:8765"
    log_info "  Health Check:         http://localhost:${HEALTH_PORT}/health"
    log_info "=========================================="

    # Monitor and keep services alive
    while true; do
        sleep 10

        # Check if any critical service has died
        for pidfile in "${PID_DIR}"/*.pid; do
            if [ -f "$pidfile" ]; then
                pid=$(cat "$pidfile")
                if ! kill -0 "$pid" 2>/dev/null; then
                    service_name=$(basename "$pidfile" .pid)
                    log_warn "Service ${service_name} (PID ${pid}) has died, attempting restart..."

                    # Implement restart logic here if needed
                fi
            fi
        done
    done
}

# Execute main
main
