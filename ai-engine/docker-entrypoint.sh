#!/bin/bash
set -e

# First run with empty volume: copy pre-downloaded model
if [ ! -f /models/yolo11n.pt ]; then
    echo "Copying YOLO model to volume..."
    cp /app/yolo11n.pt /models/yolo11n.pt
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8001
