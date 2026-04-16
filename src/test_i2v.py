import json
import urllib.request
import random

COMFYUI_URL = "http://localhost:8188"

# Note: wan model goes in diffusion_models, not checkpoints
# Need to use UNETLoader instead of CheckpointLoaderSimple for diffusion_models
workflow = {
    "1": {
        "class_type": "UNETLoader",
        "_meta": {"title": "Load Wan I2V"},
        "inputs": {
            "unet_name": "wan2.2-i2v-rapid-aio.safetensors",
            "weight_dtype": "default"
        }
    },
    "1b": {
        "class_type": "DualCLIPLoader",
        "_meta": {"title": "Load CLIP"},
        "inputs": {
            "clip_name1": "umt5xxl_fp8_e4m3fn.safetensors",
            "clip_name2": "open_clip_g.safetensors",
            "type": "wan"
        }
    },
    "1c": {
        "class_type": "VAELoader",
        "_meta": {"title": "Load VAE"},
        "inputs": {
            "vae_name": "ae.safetensors"
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
        "_meta": {"title": "Positive"},
        "inputs": {
            "clip": ["1b", 0],
            "text": "The woman starts walking forward with confidence, hair bouncing with each step, slight smile, city life moving around her, smooth forward walking motion"
        }
    },
    "4": {
        "class_type": "CLIPTextEncode",
        "_meta": {"title": "Negative"},
        "inputs": {
            "clip": ["1b", 0],
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
            "vae": ["1c", 0],
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
            "vae": ["1c", 0]
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

# First check what's available
req = urllib.request.Request(f"{COMFYUI_URL}/object_info/UNETLoader")
try:
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read().decode())
    print("Available UNETs:", data["UNETLoader"]["input"]["required"]["unet_name"][0])
except:
    print("UNETLoader not available, trying CheckpointLoaderSimple")

req2 = urllib.request.Request(f"{COMFYUI_URL}/object_info/CLIPVisionLoader")
try:
    resp2 = urllib.request.urlopen(req2)
    data2 = json.loads(resp2.read().decode())
    print("Available CLIP Vision:", data2["CLIPVisionLoader"]["input"]["required"]["clip_vision_name"][0])
except:
    print("CLIPVisionLoader issue")

req3 = urllib.request.Request(f"{COMFYUI_URL}/object_info/DualCLIPLoader")
try:
    resp3 = urllib.request.urlopen(req3)
    data3 = json.loads(resp3.read().decode())
    print("Available CLIPs:", data3["DualCLIPLoader"]["input"]["required"]["clip_name1"][0][:5])
except:
    print("DualCLIPLoader issue")

req4 = urllib.request.Request(f"{COMFYUI_URL}/object_info/VAELoader")
try:
    resp4 = urllib.request.urlopen(req4)
    data4 = json.loads(resp4.read().decode())
    print("Available VAEs:", data4["VAELoader"]["input"]["required"]["vae_name"][0])
except:
    print("VAELoader issue")
