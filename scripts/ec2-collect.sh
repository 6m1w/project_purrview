#!/usr/bin/env bash
# PurrView data collection script for EC2
# Usage:
#   ./scripts/ec2-collect.sh setup     # first time: install deps
#   ./scripts/ec2-collect.sh start     # start 24h collection (background)
#   ./scripts/ec2-collect.sh status    # check progress
#   ./scripts/ec2-collect.sh stop      # stop collection
#   ./scripts/ec2-collect.sh disk      # check disk usage
#   ./scripts/ec2-collect.sh preview   # show latest frames + motion scores

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORKER_DIR="$PROJECT_ROOT/apps/worker"
VENV="$WORKER_DIR/.venv"
DATA_DIR="$WORKER_DIR/data"
PID_FILE="$WORKER_DIR/.collect.pid"
LOG_FILE="$WORKER_DIR/collect.log"

# Default collection settings
DURATION="${DURATION:-86400}"      # 24 hours
INTERVAL="${INTERVAL:-5}"          # 5 seconds between frames

setup() {
    echo "=== PurrView Collection Setup ==="

    # Check Python 3.12+
    if ! command -v python3 &>/dev/null; then
        echo "Installing Python 3.12..."
        sudo apt-get update
        sudo apt-get install -y python3.12 python3.12-venv python3-pip
    fi
    python3 --version

    # Check ffmpeg
    if ! command -v ffmpeg &>/dev/null; then
        echo "Installing ffmpeg..."
        sudo apt-get update
        sudo apt-get install -y ffmpeg
    fi
    ffmpeg -version | head -1

    # Check OpenCV system deps
    sudo apt-get install -y --no-install-recommends libgl1-mesa-glx libglib2.0-0 2>/dev/null || true

    # Create venv and install
    if [ ! -d "$VENV" ]; then
        echo "Creating virtual environment..."
        python3 -m venv "$VENV"
    fi
    echo "Installing dependencies..."
    "$VENV/bin/pip" install --upgrade pip -q
    "$VENV/bin/pip" install -e "$WORKER_DIR" -q

    # Check .env
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        echo ""
        echo "WARNING: .env not found at $PROJECT_ROOT/.env"
        echo "Copy .env.example and fill in values:"
        echo "  cp $PROJECT_ROOT/.env.example $PROJECT_ROOT/.env"
        echo "  vim $PROJECT_ROOT/.env"
        exit 1
    fi

    echo ""
    echo "=== Setup complete ==="
    echo "Run: ./scripts/ec2-collect.sh start"
}

start() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "Collection already running (PID $(cat "$PID_FILE"))"
        echo "Use './scripts/ec2-collect.sh stop' first"
        exit 1
    fi

    echo "Starting collection: interval=${INTERVAL}s, duration=${DURATION}s (~$((DURATION/3600))h)"
    echo "Log: $LOG_FILE"

    mkdir -p "$DATA_DIR"

    cd "$WORKER_DIR"
    nohup "$VENV/bin/python" -m src.collect \
        --duration "$DURATION" \
        --interval "$INTERVAL" \
        --output data \
        > "$LOG_FILE" 2>&1 &

    echo $! > "$PID_FILE"
    echo "Started (PID $!)"
    echo ""
    echo "Check progress:  ./scripts/ec2-collect.sh status"
    echo "Stop:            ./scripts/ec2-collect.sh stop"
}

stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo "No collection running (no PID file)"
        exit 0
    fi

    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Stopping collection (PID $PID)..."
        kill "$PID"
        # Wait for graceful shutdown
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
    echo "=== Collection Status ==="

    # Process status
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "Status:  RUNNING (PID $(cat "$PID_FILE"))"
    else
        echo "Status:  STOPPED"
    fi

    # Latest log lines
    if [ -f "$LOG_FILE" ]; then
        echo ""
        echo "--- Last 5 log lines ---"
        tail -5 "$LOG_FILE"
    fi

    # Data stats
    echo ""
    disk_usage
}

disk_usage() {
    echo "--- Disk Usage ---"
    if [ -d "$DATA_DIR" ]; then
        TOTAL_FRAMES=$(find "$DATA_DIR" -name "*.jpg" 2>/dev/null | wc -l | tr -d ' ')
        TOTAL_SIZE=$(du -sh "$DATA_DIR" 2>/dev/null | cut -f1)
        echo "Frames:  $TOTAL_FRAMES"
        echo "Size:    $TOTAL_SIZE"

        # Per-day breakdown
        echo ""
        echo "--- Per Day ---"
        for day_dir in "$DATA_DIR"/*/; do
            if [ -d "$day_dir" ]; then
                DAY=$(basename "$day_dir")
                COUNT=$(find "$day_dir" -name "*.jpg" | wc -l | tr -d ' ')
                SIZE=$(du -sh "$day_dir" | cut -f1)
                # Count motion frames from metadata
                MOTION=0
                if [ -f "$day_dir/metadata.json" ]; then
                    MOTION=$(grep -c '"has_motion": true' "$day_dir/metadata.json" 2>/dev/null || echo 0)
                fi
                echo "  $DAY: $COUNT frames ($SIZE), $MOTION with motion"
            fi
        done
    else
        echo "No data collected yet"
    fi

    echo ""
    echo "--- EC2 Disk ---"
    df -h / | tail -1 | awk '{print "Total: "$2"  Used: "$3"  Free: "$4"  ("$5" used)"}'
}

preview() {
    # Find today's data dir
    TODAY=$(date -u +%Y-%m-%d)
    TODAY_DIR="$DATA_DIR/$TODAY"

    if [ ! -d "$TODAY_DIR" ]; then
        echo "No data for today ($TODAY)"
        exit 1
    fi

    echo "=== Latest Frames ($TODAY) ==="

    if [ -f "$TODAY_DIR/metadata.json" ]; then
        # Show last 10 entries
        echo "--- Last 10 frames ---"
        "$VENV/bin/python3" -c "
import json
with open('$TODAY_DIR/metadata.json') as f:
    meta = json.load(f)
for m in meta[-10:]:
    flag = '*** ' if m['has_motion'] else '    '
    print(f\"{flag}{m['filename']}  motion={m['motion_score']:>6,}  {m['timestamp']}\")
print()
total = len(meta)
motion = sum(1 for m in meta if m['has_motion'])
print(f'Total: {total} frames, {motion} with motion ({motion*100//max(total,1)}%)')
"
    fi
}

# --- Main ---
case "${1:-help}" in
    setup)   setup ;;
    start)   start ;;
    stop)    stop ;;
    status)  status ;;
    disk)    disk_usage ;;
    preview) preview ;;
    *)
        echo "PurrView Data Collection"
        echo ""
        echo "Usage: $0 <command>"
        echo ""
        echo "Commands:"
        echo "  setup     Install dependencies (first time)"
        echo "  start     Start 24h collection (background)"
        echo "  stop      Stop collection"
        echo "  status    Check progress & disk usage"
        echo "  disk      Show disk usage details"
        echo "  preview   Show latest motion scores"
        echo ""
        echo "Environment:"
        echo "  DURATION=86400  Collection duration in seconds (default: 24h)"
        echo "  INTERVAL=2      Seconds between frames (default: 2)"
        echo ""
        echo "Examples:"
        echo "  $0 start                      # 24h, every 2s"
        echo "  DURATION=3600 $0 start        # 1h test run"
        echo "  INTERVAL=5 $0 start           # every 5s (saves disk)"
        ;;
esac
