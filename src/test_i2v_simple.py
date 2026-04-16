import json
import urllib.request
import random

COMFYUI_URL = "http://localhost:8188"

# Wan AIO includes CLIP + VAE, so use CheckpointLoaderSimple
workflow = {
    "1": {
        "class_type": "CheckpointLoaderSimple",
        "inputs": {
            "ckpt_name": "wan2.2-i2v-rapid-aio.safetensors"
        }
    },
    "12": {
        "class_type": "CLIPVisionLoader",
        "inputs": {
            "clip_vision_name": "clip-vision_vit-h.safetensors"
        }
    },
    "10": {
        "class_type": "LoadImage",
        "inputs": {
            "image": "mia_urban.png",
            "upload": "image"
        }
    },
    "5": {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "clip": ["1", 1],
            "text": "The woman starts walking forward confidently, hair bouncing with each step, slight smile, smooth natural walking motion"
        }
    },
    "4": {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "clip": ["1", 1],
            "text": ""
        }
    },
    "11": {
        "class_type": "CLIPVisionEncode",
        "inputs": {
            "clip_vision": ["12", 0],
            "image": ["10", 0],
            "crop": "center"
        }
    },
    "9": {
        "class_type": "WanImageToVideo",
        "inputs": {
            "positive": ["5", 0],
            "negative": ["4", 0],
            "vae": ["1", 2],
            "clip_vision_output": ["11", 0],
            "start_image": ["10", 0],
            "width": 640,
            "height": 640,
            "length": 81,
            "batch_size": 1
        }
    },
    "2": {
        "class_type": "ModelSamplingSD3",
        "inputs": {
            "model": ["1", 0],
            "shift": 8.0
        }
    },
    "3": {
        "class_type": "KSampler",
        "inputs": {
            "model": ["2", 0],
            "positive": ["9", 0],
            "negative": ["9", 1],
            "latent_image": ["9", 2],
            "seed": random.randint(1, 999999999),
            "steps": 4,
            "cfg": 1.0,
            "sampler_name": "sa_solver",
            "scheduler": "beta",
            "denoise": 1.0
        }
    },
    "7": {
        "class_type": "VAEDecode",
        "inputs": {
            "samples": ["3", 0],
            "vae": ["1", 2]
        }
    },
    "8": {
        "class_type": "VHS_VideoCombine",
        "inputs": {
            "images": ["7", 0],
            "frame_rate": 24,
            "loop_count": 0,
            "filename_prefix": "i2v_test",
            "format": "video/h264-mp4",
            "pix_fmt": "yuv420p",
            "crf": 19,
            "save_metadata": True,
            "trim_to_audio": False,
            "pingpong": False,
            "save_output": True
        }
    }
}

payload = json.dumps({"prompt": workflow, "client_id": "i2v-test"}).encode()
req = urllib.request.Request(
    f"{COMFYUI_URL}/api/prompt",
    data=payload,
    headers={"Content-Type": "application/json"}
)
try:
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode())
    print(f"QUEUED: {result['prompt_id']}")
    print(f"Errors: {result['node_errors']}")
except urllib.error.HTTPError as e:
    error = json.loads(e.read().decode())
    print(f"Error {e.code}:")
    print(json.dumps(error, indent=2))
