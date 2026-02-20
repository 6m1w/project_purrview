#!/usr/bin/env bash
# PurrView real-time pipeline worker for EC2
# Usage:
#   ./scripts/ec2-worker.sh start     # start pipeline (background)
#   ./scripts/ec2-worker.sh status    # check progress
#   ./scripts/ec2-worker.sh stop      # stop pipeline
#   ./scripts/ec2-worker.sh logs      # tail live logs
#   ./scripts/ec2-worker.sh cleanup   # delete data older than 7 days

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORKER_DIR="$PROJECT_ROOT/apps/worker"
VENV="$WORKER_DIR/.venv"
DATA_DIR="$WORKER_DIR/data"
PID_FILE="$WORKER_DIR/.worker.pid"
LOG_FILE="$WORKER_DIR/worker.log"

RETENTION_DAYS="${RETENTION_DAYS:-7}"

start() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "Worker already running (PID $(cat "$PID_FILE"))"
        echo "Use './scripts/ec2-worker.sh stop' first"
        exit 1
    fi

    # Verify setup
    if [ ! -d "$VENV" ]; then
        echo "ERROR: venv not found. Run './scripts/ec2-collect.sh setup' first."
        exit 1
    fi
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        echo "ERROR: .env not found at $PROJECT_ROOT/.env"
        exit 1
    fi

    echo "Starting PurrView worker pipeline..."
    echo "Log: $LOG_FILE"

    cd "$WORKER_DIR"
    nohup "$VENV/bin/python" -u -m src.main \
        > "$LOG_FILE" 2>&1 &

    echo $! > "$PID_FILE"
    echo "Started (PID $!)"
    echo ""
    echo "Check:  ./scripts/ec2-worker.sh status"
    echo "Logs:   ./scripts/ec2-worker.sh logs"
    echo "Stop:   ./scripts/ec2-worker.sh stop"
}

stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo "No worker running (no PID file)"
        exit 0
    fi

    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Stopping worker (PID $PID)..."
        kill "$PID"
        for i in $(seq 1 10); do
            if ! kill -0 "$PID" 2>/dev/null; then
                break
            fi
            sleep 1
        done
        echo "Stopped"
    else
        echo "Process $PID not running"
    fi
    rm -f "$PID_FILE"
}

status() {
    echo "=== PurrView Worker Status ==="

    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        PID=$(cat "$PID_FILE")
        UPTIME=$(ps -o etime= -p "$PID" 2>/dev/null | tr -d ' ')
        echo "Status:  RUNNING (PID $PID, uptime $UPTIME)"
    else
        echo "Status:  STOPPED"
    fi

    # Latest log lines
    if [ -f "$LOG_FILE" ]; then
        echo ""
        echo "--- Last 10 log lines ---"
        tail -10 "$LOG_FILE"
    fi

    # DB event count (last 24h)
    echo ""
    echo "--- Disk ---"
    df -h / | tail -1 | awk '{print "Total: "$2"  Used: "$3"  Free: "$4"  ("$5" used)"}'

    if [ -d "$DATA_DIR" ]; then
        DATA_SIZE=$(du -sh "$DATA_DIR" 2>/dev/null | cut -f1)
        echo "Data dir: $DATA_SIZE"
    fi
}

logs() {
    if [ ! -f "$LOG_FILE" ]; then
        echo "No log file found"
        exit 1
    fi
    tail -f "$LOG_FILE"
}

cleanup() {
    echo "=== Data Cleanup (keep last ${RETENTION_DAYS} days) ==="

    if [ ! -d "$DATA_DIR" ]; then
        echo "No data directory"
        exit 0
    fi

    CUTOFF=$(date -u -d "${RETENTION_DAYS} days ago" +%Y-%m-%d)
    echo "Cutoff date: $CUTOFF (deleting older)"

    DELETED=0
    for day_dir in "$DATA_DIR"/????-??-??/; do
        if [ -d "$day_dir" ]; then
            DAY=$(basename "$day_dir")
            if [[ "$DAY" < "$CUTOFF" ]]; then
                SIZE=$(du -sh "$day_dir" | cut -f1)
                echo "  Deleting $DAY ($SIZE)..."
                rm -rf "$day_dir"
                DELETED=$((DELETED + 1))
            fi
        fi
    done

    if [ "$DELETED" -eq 0 ]; then
        echo "Nothing to clean up"
    else
        echo "Deleted $DELETED day(s)"
    fi
}

install_cron() {
    # Install daily cleanup cron at 03:00 UTC
    CRON_CMD="0 3 * * * $PROJECT_ROOT/scripts/ec2-worker.sh cleanup >> $WORKER_DIR/cleanup.log 2>&1"

    if crontab -l 2>/dev/null | grep -q "ec2-worker.sh cleanup"; then
        echo "Cron already installed"
    else
        (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
        echo "Cron installed: daily cleanup at 03:00 UTC"
    fi
    echo ""
    echo "Current crontab:"
    crontab -l
}

# --- Main ---
case "${1:-help}" in
    start)   start ;;
    stop)    stop ;;
    status)  status ;;
    logs)    logs ;;
    cleanup) cleanup ;;
    cron)    install_cron ;;
    *)
        echo "PurrView Real-time Worker"
        echo ""
        echo "Usage: $0 <command>"
        echo ""
        echo "Commands:"
        echo "  start     Start the real-time pipeline (background)"
        echo "  stop      Stop the pipeline"
        echo "  status    Check worker status & recent logs"
        echo "  logs      Tail live worker logs"
        echo "  cleanup   Delete data older than ${RETENTION_DAYS} days"
        echo "  cron      Install daily cleanup cron job (03:00 UTC)"
        echo ""
        echo "Environment:"
        echo "  RETENTION_DAYS=7   Days of data to keep (default: 7)"
        ;;
esac
