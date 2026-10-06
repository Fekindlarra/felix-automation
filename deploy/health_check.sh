#!/bin/bash
# Production health checks and monitoring script for Felix Automation
# Runs continuously and alerts on issues

set -euo pipefail

ENVIRONMENT=${1:-production}
CHECK_INTERVAL=${2:-60}  # seconds
LOG_FILE="/var/log/felix-automation/health_check.log"

mkdir -p "$(dirname "$LOG_FILE")"

# Thresholds
HTTP_TIMEOUT=10
RESPONSE_TIME_WARN=1000  # milliseconds
RESPONSE_TIME_CRIT=2000  # milliseconds
DISK_USAGE_WARN=80      # percent
MEMORY_USAGE_WARN=85    # percent
CPU_USAGE_WARN=80       # percent

# Alert tracking
declare -A alert_status
declare -A alert_timestamp

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

alert() {
    local severity=$1
    local component=$2
    local message=$3

    local timestamp=$(date +%s)
    local key="${component}_${severity}"

    # Deduplicate alerts - only alert once per minute
    if [ -n "${alert_timestamp[$key]:-}" ]; then
        local time_since=$((timestamp - alert_timestamp[$key]))
        if [ $time_since -lt 60 ]; then
            return
        fi
    fi

    alert_timestamp[$key]=$timestamp
    alert_status[$key]=$severity

    log "[$severity] $component: $message"

    # Send to monitoring system
    send_alert "$severity" "$component" "$message"
}

send_alert() {
    local severity=$1
    local component=$2
    local message=$3

    # Send to Datadog
    if [ -n "${DATADOG_API_KEY:-}" ]; then
        curl -X POST "https://api.datadoghq.com/api/v1/events" \
            -H "DD-API-KEY: $DATADOG_API_KEY" \
            -d "{
                \"title\": \"Felix Automation - $component\",
                \"text\": \"$message\",
                \"priority\": \"$([ \"$severity\" = \"CRITICAL\" ] && echo 'high' || echo 'normal')\",
                \"tags\": [\"environment:$ENVIRONMENT\", \"component:$component\", \"severity:$severity\"]
            }" 2>/dev/null || true
    fi

    # Send to Slack
    if [ -n "${SLACK_WEBHOOK:-}" ]; then
        local color=$([ "$severity" = "CRITICAL" ] && echo "danger" || echo "warning")
        curl -X POST "$SLACK_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d "{
                \"attachments\": [{
                    \"color\": \"$color\",
                    \"title\": \"[$(echo $severity | cut -c1)]Felix Health Alert\",
                    \"text\": \"**$component**: $message\",
                    \"footer\": \"Felix Automation - $ENVIRONMENT\"
                }]
            }" 2>/dev/null || true
    fi
}

# Health check functions
check_api_health() {
    local endpoint="http://localhost:5000/health"
    local start_time=$(date +%s%N | cut -b1-13)

    local http_code=$(curl -s -o /dev/null -w "%{http_code}" -m "$HTTP_TIMEOUT" "$endpoint" 2>/dev/null || echo "000")
    local end_time=$(date +%s%N | cut -b1-13)
    local response_time=$((end_time - start_time))

    if [ "$http_code" != "200" ]; then
        alert "CRITICAL" "API" "Health endpoint returned HTTP $http_code"
        return 1
    fi

    if [ $response_time -gt $RESPONSE_TIME_CRIT ]; then
        alert "CRITICAL" "API" "Response time ${response_time}ms exceeds critical threshold"
        return 1
    elif [ $response_time -gt $RESPONSE_TIME_WARN ]; then
        alert "WARNING" "API" "Response time ${response_time}ms exceeds warning threshold"
    fi

    return 0
}

check_database_health() {
    local db_status=$(docker compose -f /opt/felix-automation/docker-compose.prod.yml \
        exec -T db pg_isready -U "${DB_USER:-felix_user}" 2>/dev/null || echo "not running")

    if [ "$db_status" != "accepting connections" ]; then
        alert "CRITICAL" "Database" "PostgreSQL is not accepting connections"
        return 1
    fi

    # Check connection pool
    local idle_connections=$(docker compose -f /opt/felix-automation/docker-compose.prod.yml \
        exec -T db psql -U "${DB_USER:-felix_user}" -d felix_automation \
        -t -c "SELECT count(*) FROM pg_stat_activity WHERE state='idle';" 2>/dev/null || echo "0")

    if [ "$idle_connections" -gt 50 ]; then
        alert "WARNING" "Database" "High number of idle connections: $idle_connections"
    fi

    return 0
}

check_cache_health() {
    local redis_ping=$(docker compose -f /opt/felix-automation/docker-compose.prod.yml \
        exec -T cache redis-cli ping 2>/dev/null || echo "PONG")

    if [ "$redis_ping" != "PONG" ]; then
        alert "CRITICAL" "Cache" "Redis is not responding"
        return 1
    fi

    return 0
}

check_disk_usage() {
    local usage=$(df /opt/felix-automation | awk 'NR==2 {print $5}' | sed 's/%//')

    if [ "$usage" -ge 95 ]; then
        alert "CRITICAL" "Disk" "Disk usage is ${usage}% - critical space issue"
        return 1
    elif [ "$usage" -ge $DISK_USAGE_WARN ]; then
        alert "WARNING" "Disk" "Disk usage is ${usage}% - approaching limit"
    fi

    return 0
}

check_memory_usage() {
    local memory_info=$(free | grep Mem)
    local total=$(echo $memory_info | awk '{print $2}')
    local used=$(echo $memory_info | awk '{print $3}')
    local usage=$((used * 100 / total))

    if [ "$usage" -ge 95 ]; then
        alert "CRITICAL" "Memory" "Memory usage is ${usage}% - critical level"
        return 1
    elif [ "$usage" -ge $MEMORY_USAGE_WARN ]; then
        alert "WARNING" "Memory" "Memory usage is ${usage}%"
    fi

    return 0
}

check_cpu_usage() {
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}' | cut -d. -f1)

    if [ "$cpu_usage" -ge 95 ]; then
        alert "CRITICAL" "CPU" "CPU usage is ${cpu_usage}% - critical level"
        return 1
    elif [ "$cpu_usage" -ge $CPU_USAGE_WARN ]; then
        alert "WARNING" "CPU" "CPU usage is ${cpu_usage}%"
    fi

    return 0
}

check_container_status() {
    local containers=("felix_app_prod" "felix_db_prod" "felix_cache_prod" "felix_proxy_prod")

    for container in "${containers[@]}"; do
        local status=$(docker inspect -f '{{.State.Status}}' "$container" 2>/dev/null || echo "not_found")

        if [ "$status" != "running" ]; then
            alert "CRITICAL" "Container" "Container $container is not running (status: $status)"
        fi
    done

    return 0
}

check_websocket_connections() {
    # Check for active WebSocket connections
    local ws_connections=$(docker compose -f /opt/felix-automation/docker-compose.prod.yml \
        exec -T app python -c "
import subprocess
import json
result = subprocess.run(['netstat', '-an'], capture_output=True, text=True)
ws_conns = len([line for line in result.stdout.split('\n') if ':5000' in line and 'ESTABLISHED' in line])
print(ws_conns)
" 2>/dev/null || echo "0")

    if [ "$ws_connections" -lt 1 ]; then
        alert "WARNING" "WebSocket" "No active WebSocket connections detected"
    fi

    return 0
}

check_alert_queue() {
    # Check alert queue depth in database
    local queue_depth=$(docker compose -f /opt/felix-automation/docker-compose.prod.yml \
        exec -T db psql -U "${DB_USER:-felix_user}" -d felix_automation \
        -t -c "SELECT count(*) FROM alerts WHERE status='pending';" 2>/dev/null || echo "0")

    if [ "$queue_depth" -gt 1000 ]; then
        alert "WARNING" "AlertQueue" "Alert queue depth is $queue_depth"
    fi

    return 0
}

check_webhook_health() {
    # Check webhook delivery success rate (last hour)
    local success_rate=$(docker compose -f /opt/felix-automation/docker-compose.prod.yml \
        exec -T db psql -U "${DB_USER:-felix_user}" -d felix_automation \
        -t -c "
SELECT ROUND(100.0 * COUNT(CASE WHEN status='delivered' THEN 1 END) / COUNT(*), 2)
FROM webhook_deliveries
WHERE created_at > NOW() - INTERVAL '1 hour';
" 2>/dev/null || echo "0")

    if (( $(echo "$success_rate < 95" | bc -l) )); then
        alert "WARNING" "Webhook" "Webhook delivery success rate is ${success_rate}%"
    fi

    return 0
}

# Main monitoring loop
run_health_checks() {
    log "Starting health checks (interval: ${CHECK_INTERVAL}s)"

    while true; do
        local check_start=$(date +%s)

        check_api_health
        check_database_health
        check_cache_health
        check_disk_usage
        check_memory_usage
        check_cpu_usage
        check_container_status
        check_websocket_connections
        check_alert_queue
        check_webhook_health

        local check_end=$(date +%s)
        local check_duration=$((check_end - check_start))
        local sleep_time=$((CHECK_INTERVAL - check_duration))

        if [ $sleep_time -gt 0 ]; then
            sleep $sleep_time
        fi
    done
}

# Run health checks
run_health_checks
