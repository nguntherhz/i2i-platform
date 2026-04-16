#!/usr/bin/env python3
"""
ComfyUI Process Watcher & Auto-Restart
Monitors ComfyUI health, cleans VRAM cache, and restarts on failure.
Run as: python3 comfyui_watcher.py
"""

import subprocess
import time
import urllib.request
import json
import os
import signal
import sys
import gc

COMFYUI_DIR = "/workspace/runpod-slim/ComfyUI"
COMFYUI_PORT = 8188
COMFYUI_HOST = "0.0.0.0"
HEALTH_CHECK_INTERVAL = 30  # seconds
VRAM_CLEANUP_INTERVAL = 300  # 5 minutes
MAX_RESTART_ATTEMPTS = 5
RESTART_COOLDOWN = 10  # seconds between restart attempts

LOG_FILE = "/tmp/comfyui_watcher.log"


def log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def is_comfyui_running():
    """Check if ComfyUI process is alive."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "python3 main.py"],
            capture_output=True, text=True
        )
        return result.returncode == 0
    except:
        return False


def is_comfyui_healthy():
    """Check if ComfyUI API responds."""
    try:
        req = urllib.request.Request(
            f"http://localhost:{COMFYUI_PORT}/api/system_stats",
            method="GET"
        )
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode())
        return "system" in data
    except:
        return False


def get_comfyui_pid():
    """Get ComfyUI main process PID."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "python3 main.py"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            pids = result.stdout.strip().split("\n")
            return int(pids[0])
    except:
        pass
    return None


def kill_comfyui():
    """Kill all ComfyUI processes."""
    log("Killing ComfyUI processes...")
    subprocess.run(["pkill", "-f", "python3 main.py"], capture_output=True)
    time.sleep(3)
    # Force kill if still running
    subprocess.run(["pkill", "-9", "-f", "python3 main.py"], capture_output=True)
    time.sleep(2)


def start_comfyui():
    """Start ComfyUI with CORS enabled."""
    log(f"Starting ComfyUI on port {COMFYUI_PORT} with CORS...")
    env = os.environ.copy()
    process = subprocess.Popen(
        [
            "python3", "main.py",
            "--listen", COMFYUI_HOST,
            "--port", str(COMFYUI_PORT),
            "--enable-cors-header"
        ],
        cwd=COMFYUI_DIR,
        stdout=open("/tmp/comfyui.log", "w"),
        stderr=subprocess.STDOUT,
        env=env
    )
    log(f"ComfyUI started with PID {process.pid}")
    return process


def cleanup_vram():
    """Free VRAM by calling ComfyUI's free endpoint and Python GC."""
    try:
        # ComfyUI free memory endpoint
        payload = json.dumps({"unload_models": True, "free_memory": True}).encode()
        req = urllib.request.Request(
            f"http://localhost:{COMFYUI_PORT}/api/free",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(req, timeout=10)
        log("VRAM cleanup: unloaded models and freed memory via API")
    except Exception as e:
        log(f"VRAM cleanup API failed: {e}")

    # Python garbage collection
    gc.collect()


def get_vram_usage():
    """Get current VRAM usage in MB."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            used, total = result.stdout.strip().split(", ")
            return int(used), int(total)
    except:
        pass
    return 0, 0


def cleanup_output_cache():
    """Clean old output files to prevent disk bloat."""
    output_dir = os.path.join(COMFYUI_DIR, "output")
    if not os.path.exists(output_dir):
        return

    now = time.time()
    max_age = 3600 * 24  # 24 hours
    cleaned = 0

    for f in os.listdir(output_dir):
        fpath = os.path.join(output_dir, f)
        if os.path.isfile(fpath):
            age = now - os.path.getmtime(fpath)
            if age > max_age:
                os.remove(fpath)
                cleaned += 1

    if cleaned > 0:
        log(f"Disk cleanup: removed {cleaned} output files older than 24h")


def main():
    log("=" * 60)
    log("ComfyUI Watcher started")
    log(f"  Directory: {COMFYUI_DIR}")
    log(f"  Port: {COMFYUI_PORT}")
    log(f"  Health check interval: {HEALTH_CHECK_INTERVAL}s")
    log(f"  VRAM cleanup interval: {VRAM_CLEANUP_INTERVAL}s")
    log("=" * 60)

    restart_count = 0
    last_vram_cleanup = time.time()
    last_disk_cleanup = time.time()

    # Initial start if not running
    if not is_comfyui_running():
        start_comfyui()
        time.sleep(15)  # Wait for startup

    while True:
        try:
            # Health check
            process_alive = is_comfyui_running()
            api_healthy = is_comfyui_healthy() if process_alive else False

            if not process_alive:
                log("ALERT: ComfyUI process is dead!")
                if restart_count < MAX_RESTART_ATTEMPTS:
                    kill_comfyui()  # Clean up any zombies
                    start_comfyui()
                    restart_count += 1
                    log(f"Restart attempt {restart_count}/{MAX_RESTART_ATTEMPTS}")
                    time.sleep(20)  # Wait for startup
                else:
                    log(f"CRITICAL: Max restart attempts ({MAX_RESTART_ATTEMPTS}) reached. Waiting 60s before reset.")
                    time.sleep(60)
                    restart_count = 0
                continue

            if process_alive and not api_healthy:
                log("WARNING: ComfyUI process alive but API not responding. Waiting...")
                time.sleep(15)
                if not is_comfyui_healthy():
                    log("API still not responding. Force restarting...")
                    kill_comfyui()
                    start_comfyui()
                    restart_count += 1
                    time.sleep(20)
                continue

            # Reset restart counter on successful health check
            if restart_count > 0:
                log(f"ComfyUI recovered. Resetting restart counter.")
                restart_count = 0

            # VRAM cleanup
            now = time.time()
            if now - last_vram_cleanup > VRAM_CLEANUP_INTERVAL:
                used, total = get_vram_usage()
                usage_pct = (used / total * 100) if total > 0 else 0
                log(f"VRAM: {used}MB / {total}MB ({usage_pct:.0f}%)")

                if usage_pct > 90:
                    log("VRAM > 90%! Running emergency cleanup...")
                    cleanup_vram()
                    time.sleep(5)
                    used2, _ = get_vram_usage()
                    log(f"VRAM after cleanup: {used2}MB")

                last_vram_cleanup = now

            # Disk cleanup (every hour)
            if now - last_disk_cleanup > 3600:
                cleanup_output_cache()
                last_disk_cleanup = now

            time.sleep(HEALTH_CHECK_INTERVAL)

        except KeyboardInterrupt:
            log("Watcher stopped by user")
            sys.exit(0)
        except Exception as e:
            log(f"Watcher error: {e}")
            time.sleep(10)


if __name__ == "__main__":
    main()
