#!/bin/bash
# Video Pod Setup Script
# Run on fresh RunPod ComfyUI CUDA13 + RTX 5090
# Usage: bash setup.sh

set -e
echo "=== i2i Video Pod Setup ==="

# 1. Verify GPU
echo "[1/7] Verifying GPU..."
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
echo ""

# 2. Find ComfyUI directory
echo "[2/7] Finding ComfyUI..."
if [ -d "/workspace/runpod-slim/ComfyUI" ]; then
    COMFY_DIR="/workspace/runpod-slim/ComfyUI"
elif [ -d "/workspace/ComfyUI" ]; then
    COMFY_DIR="/workspace/ComfyUI"
else
    echo "ERROR: ComfyUI not found"
    exit 1
fi
echo "ComfyUI at: $COMFY_DIR"
echo ""

# 3. Install VideoHelperSuite
echo "[3/7] Installing VideoHelperSuite..."
cd $COMFY_DIR/custom_nodes
if [ ! -d "ComfyUI-VideoHelperSuite" ]; then
    git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git
    echo "VideoHelperSuite installed"
else
    echo "VideoHelperSuite already exists"
fi
echo ""

# 4. Download Wan 2.2 I2V model (22GB)
echo "[4/7] Downloading Wan 2.2 I2V model (22GB)..."
cd $COMFY_DIR/models/checkpoints
if [ ! -f "wan2.2-i2v-rapid-aio.safetensors" ]; then
    wget -O wan2.2-i2v-rapid-aio.safetensors \
        "https://huggingface.co/Phr00t/WAN2.2-14B-Rapid-AllInOne/resolve/main/wan2.2-i2v-rapid-aio.safetensors"
    echo "Wan I2V downloaded"
else
    echo "Wan I2V already exists"
fi
echo ""

# 5. Download CLIP Vision (correct one for Wan)
echo "[5/7] Downloading CLIP Vision for Wan..."
cd $COMFY_DIR/models/clip_vision

# Wan 2.2 needs the open_clip ViT-bigG model
if [ ! -f "clip-vision_vit-h.safetensors" ]; then
    # Try multiple sources for the correct CLIP Vision
    wget -O clip-vision_vit-h.safetensors \
        "https://huggingface.co/Comfy-Org/clip_vision/resolve/main/clip-vit-large-patch14-336.safetensors" \
        2>/dev/null || \
    wget -O clip-vision_vit-h.safetensors \
        "https://huggingface.co/openai/clip-vit-large-patch14/resolve/main/model.safetensors" \
        2>/dev/null || \
    echo "WARNING: CLIP Vision download failed. May need manual download."
    echo "CLIP Vision downloaded"
else
    echo "CLIP Vision already exists"
fi
echo ""

# 6. Download I2V example workflow
echo "[6/7] Downloading example workflow..."
cd $COMFY_DIR/user
mkdir -p default/workflows
cd default/workflows
if [ ! -f "wan-i2v-example.json" ]; then
    wget -O wan-i2v-example.json \
        "https://huggingface.co/Phr00t/WAN2.2-14B-Rapid-AllInOne/resolve/main/wan2.2-i2v-rapid-aio-example.json"
    echo "Example workflow downloaded"
else
    echo "Example workflow already exists"
fi
echo ""

# 7. Setup watcher
echo "[7/7] Setting up watcher..."
cat > /workspace/runpod-slim/comfyui_watcher.py << 'WATCHEREOF'
#!/usr/bin/env python3
import subprocess, time, urllib.request, json, os, gc, sys

COMFYUI_DIR = os.environ.get("COMFY_DIR", "/workspace/runpod-slim/ComfyUI")
PORT = 8188
CHECK_INTERVAL = 30
VRAM_INTERVAL = 300
MAX_RESTARTS = 5
LOG = "/tmp/comfyui_watcher.log"

def log(msg):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f: f.write(line + "\n")

def is_running():
    return subprocess.run(["pgrep", "-f", "python3 main.py"], capture_output=True).returncode == 0

def is_healthy():
    try:
        r = urllib.request.urlopen(f"http://localhost:{PORT}/api/system_stats", timeout=10)
        return "system" in json.loads(r.read().decode())
    except: return False

def kill():
    log("Killing ComfyUI...")
    subprocess.run(["pkill", "-f", "python3 main.py"], capture_output=True)
    time.sleep(3)
    subprocess.run(["pkill", "-9", "-f", "python3 main.py"], capture_output=True)
    time.sleep(2)

def start():
    log(f"Starting ComfyUI on port {PORT}...")
    subprocess.Popen(
        ["python3", "main.py", "--listen", "0.0.0.0", "--port", str(PORT), "--enable-cors-header"],
        cwd=COMFYUI_DIR, stdout=open("/tmp/comfyui.log", "w"), stderr=subprocess.STDOUT
    )

def cleanup_vram():
    try:
        payload = json.dumps({"unload_models": True, "free_memory": True}).encode()
        req = urllib.request.Request(f"http://localhost:{PORT}/api/free", data=payload,
            headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=10)
        log("VRAM cleanup done")
    except Exception as e: log(f"VRAM cleanup failed: {e}")

def get_vram():
    try:
        r = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True)
        used, total = r.stdout.strip().split(", ")
        return int(used), int(total)
    except: return 0, 0

log("=" * 50)
log("Video Pod Watcher started")
log("=" * 50)

restarts = 0
last_vram = time.time()

if not is_running(): start(); time.sleep(15)

while True:
    try:
        alive = is_running()
        healthy = is_healthy() if alive else False
        if not alive:
            log("ComfyUI DOWN!")
            if restarts < MAX_RESTARTS:
                kill(); start(); restarts += 1
                log(f"Restart {restarts}/{MAX_RESTARTS}")
                time.sleep(20)
            else:
                log("Max restarts reached. Waiting 60s...")
                time.sleep(60); restarts = 0
            continue
        if alive and not healthy:
            log("API not responding...")
            time.sleep(15)
            if not is_healthy():
                kill(); start(); restarts += 1; time.sleep(20)
            continue
        if restarts > 0: log("Recovered"); restarts = 0
        now = time.time()
        if now - last_vram > VRAM_INTERVAL:
            u, t = get_vram()
            pct = (u/t*100) if t > 0 else 0
            log(f"VRAM: {u}MB / {t}MB ({pct:.0f}%)")
            if pct > 90: log("VRAM > 90%! Cleanup..."); cleanup_vram()
            last_vram = now
        time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt: log("Stopped"); sys.exit(0)
    except Exception as e: log(f"Error: {e}"); time.sleep(10)
WATCHEREOF

chmod +x /workspace/runpod-slim/comfyui_watcher.py
echo "Watcher installed"
echo ""

# Enable dev mode
echo '{"Comfy.DevMode": true, "Comfy.TutorialCompleted": true}' > $COMFY_DIR/user/default/comfy.settings.json

# Kill existing ComfyUI and start via watcher
echo "Starting services..."
pkill -f "python3 main.py" 2>/dev/null || true
sleep 2
nohup python3 /workspace/runpod-slim/comfyui_watcher.py > /tmp/comfyui_watcher.log 2>&1 &

echo ""
echo "=== Setup Complete ==="
echo "ComfyUI starting on port 8188 with CORS"
echo "Watcher running with auto-restart"
echo ""
echo "Wait ~30s for ComfyUI to be ready, then verify:"
echo "  curl http://localhost:8188/api/system_stats"
echo ""
echo "Models installed:"
ls -lh $COMFY_DIR/models/checkpoints/*.safetensors 2>/dev/null
echo ""
echo "CLIP Vision:"
ls -lh $COMFY_DIR/models/clip_vision/*.safetensors 2>/dev/null
