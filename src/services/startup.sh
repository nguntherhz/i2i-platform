#!/bin/bash
# Pod startup script - run on boot
# Place in /workspace/runpod-slim/startup.sh or add to RunPod template

set -e

COMFYUI_DIR="/workspace/runpod-slim/ComfyUI"
WATCHER_SCRIPT="/workspace/runpod-slim/comfyui_watcher.py"
LOG="/tmp/startup.log"

echo "[$(date)] Starting i2i services..." | tee -a $LOG

# Kill any existing ComfyUI
pkill -f "python3 main.py" 2>/dev/null || true
pkill -f "comfyui_watcher.py" 2>/dev/null || true
sleep 2

# Start watcher (which starts ComfyUI)
echo "[$(date)] Starting ComfyUI watcher..." | tee -a $LOG
nohup python3 $WATCHER_SCRIPT > /tmp/comfyui_watcher.log 2>&1 &
echo "[$(date)] Watcher PID: $!" | tee -a $LOG

# Wait for ComfyUI to be ready
echo "[$(date)] Waiting for ComfyUI to be ready..." | tee -a $LOG
for i in $(seq 1 30); do
    if curl -s http://localhost:8188/api/system_stats > /dev/null 2>&1; then
        echo "[$(date)] ComfyUI is ready on port 8188!" | tee -a $LOG
        exit 0
    fi
    sleep 2
done

echo "[$(date)] WARNING: ComfyUI did not become ready in 60s" | tee -a $LOG
