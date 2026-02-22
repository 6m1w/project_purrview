#!/usr/bin/env bash
# PurrView Worker — systemd service management
# Usage: ./scripts/worker-service.sh {install|start|stop|restart|status|logs}

set -euo pipefail

SERVICE_NAME="purrview-worker"
SERVICE_FILE="$(cd "$(dirname "$0")" && pwd)/purrview-worker.service"

case "${1:-help}" in
  install)
    echo "Installing $SERVICE_NAME service..."
    sudo cp "$SERVICE_FILE" /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable "$SERVICE_NAME"
    echo "Service installed and enabled. Run: $0 start"
    ;;
  start)
    sudo systemctl start "$SERVICE_NAME"
    echo "Started. Check: $0 status"
    ;;
  stop)
    sudo systemctl stop "$SERVICE_NAME"
    echo "Stopped."
    ;;
  restart)
    sudo systemctl restart "$SERVICE_NAME"
    echo "Restarted. Check: $0 status"
    ;;
  status)
    systemctl status "$SERVICE_NAME" --no-pager
    ;;
  logs)
    # Show last 50 lines + follow
    journalctl -u "$SERVICE_NAME" -n 50 -f
    ;;
  *)
    echo "Usage: $0 {install|start|stop|restart|status|logs}"
    exit 1
    ;;
esac
