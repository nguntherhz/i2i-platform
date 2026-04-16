import json

OUTPUT_DIR = "/workspace/runpod-slim/ComfyUI/user/default/workflows"

# T2I with LoRA F2P - for face consistency in portrait generation
wf = {
    "id": "t2i-lora-001",
    "revision": 0,
    "last_node_id": 10,
    "last_link_id": 14,
    "nodes": [
        {
            "id": 1, "type": "CheckpointLoaderSimple",
            "pos": [-400, 30], "size": [370, 100],
            "flags": {}, "order": 0, "mode": 0,
            "inputs": [],
            "outputs": [
                {"name": "MODEL", "type": "MODEL", "links": [1]},
                {"name": "CLIP", "type": "CLIP", "links": [20]},
                {"name": "VAE", "type": "VAE", "links": [5, 6, 7]}
            ],
            "properties": {"Node name for S&R": "CheckpointLoaderSimple"},
            "widgets_values": ["Qwen-Rapid-AIO-NSFW-v18.1.safetensors"]
        },
        {
            "id": 10, "type": "LoraLoader",
            "pos": [-400, 180], "size": [370, 130],
            "flags": {}, "order": 1, "mode": 0,
            "inputs": [
                {"name": "model", "type": "MODEL", "link": 1},
                {"name": "clip", "type": "CLIP", "link": 20}
            ],
            "outputs": [
                {"name": "MODEL", "type": "MODEL", "links": [13]},
                {"name": "CLIP", "type": "CLIP", "links": [2, 4]}
            ],
            "title": "LoRA - F2P Face Consistency",
            "properties": {"Node name for S&R": "LoraLoader"},
            "widgets_values": ["Qwen-Image-Edit-F2P.safetensors", 0.7, 0.7]
        },
        {
            "id": 3, "type": "TextEncodeQwenImageEditPlus",
            "pos": [-10, 180], "size": [380, 200],
            "flags": {}, "order": 2, "mode": 0,
            "inputs": [
                {"name": "clip", "type": "CLIP", "link": 2},
                {"name": "vae", "type": "VAE", "link": 5, "shape": 7},
                {"name": "image1", "type": "IMAGE", "link": None, "shape": 7},
                {"name": "image2", "type": "IMAGE", "link": None, "shape": 7},
                {"name": "image3", "type": "IMAGE", "link": None, "shape": 7}
            ],
            "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [3]}],
            "title": "Positive Prompt",
            "properties": {"Node name for S&R": "TextEncodeQwenImageEditPlus"},
            "widgets_values": ["Full body portrait, beautiful young woman, 25 years old, photorealistic, 8k"]
        },
        {
            "id": 4, "type": "TextEncodeQwenImageEditPlus",
            "pos": [-10, 430], "size": [380, 200],
            "flags": {}, "order": 3, "mode": 0,
            "inputs": [
                {"name": "clip", "type": "CLIP", "link": 4},
                {"name": "vae", "type": "VAE", "link": 7, "shape": 7},
                {"name": "image1", "type": "IMAGE", "link": None, "shape": 7},
                {"name": "image2", "type": "IMAGE", "link": None, "shape": 7},
                {"name": "image3", "type": "IMAGE", "link": None, "shape": 7}
            ],
            "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [8]}],
            "title": "Negative Prompt",
            "properties": {"Node name for S&R": "TextEncodeQwenImageEditPlus"},
            "widgets_values": ["deformed, watermark, low quality, bad anatomy, blurry, ugly"]
        },
        {
            "id": 9, "type": "EmptyLatentImage",
            "pos": [-10, 680], "size": [270, 106],
            "flags": {}, "order": 4, "mode": 0,
            "inputs": [],
            "outputs": [{"name": "LATENT", "type": "LATENT", "links": [9]}],
            "title": "Output Size",
            "properties": {"Node name for S&R": "EmptyLatentImage"},
            "widgets_values": [768, 1024, 1]
        },
        {
            "id": 2, "type": "KSampler",
            "pos": [420, 30], "size": [270, 262],
            "flags": {}, "order": 5, "mode": 0,
            "inputs": [
                {"name": "model", "type": "MODEL", "link": 13},
                {"name": "positive", "type": "CONDITIONING", "link": 3},
                {"name": "negative", "type": "CONDITIONING", "link": 8},
                {"name": "latent_image", "type": "LATENT", "link": 9}
            ],
            "outputs": [{"name": "LATENT", "type": "LATENT", "links": [10]}],
            "properties": {"Node name for S&R": "KSampler"},
            "widgets_values": [0, "randomize", 6, 1, "euler_ancestral", "beta", 1]
        },
        {
            "id": 5, "type": "VAEDecode",
            "pos": [740, 30], "size": [140, 46],
            "flags": {}, "order": 6, "mode": 0,
            "inputs": [
                {"name": "samples", "type": "LATENT", "link": 10},
                {"name": "vae", "type": "VAE", "link": 6}
            ],
            "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [11]}],
            "properties": {"Node name for S&R": "VAEDecode"},
            "widgets_values": []
        },
        {
            "id": 6, "type": "PreviewImage",
            "pos": [740, 130], "size": [300, 350],
            "flags": {}, "order": 7, "mode": 0,
            "inputs": [{"name": "images", "type": "IMAGE", "link": 11}],
            "outputs": [],
            "properties": {"Node name for S&R": "PreviewImage"},
            "widgets_values": []
        }
    ],
    "links": [
        [1, 1, 0, 10, 0, "MODEL"],
        [2, 10, 1, 3, 0, "CLIP"],
        [3, 3, 0, 2, 1, "CONDITIONING"],
        [4, 10, 1, 4, 0, "CLIP"],
        [5, 1, 2, 3, 1, "VAE"],
        [6, 1, 2, 5, 1, "VAE"],
        [7, 1, 2, 4, 1, "VAE"],
        [8, 4, 0, 2, 2, "CONDITIONING"],
        [9, 9, 0, 2, 3, "LATENT"],
        [10, 2, 0, 5, 0, "LATENT"],
        [11, 5, 0, 6, 0, "IMAGE"],
        [13, 10, 0, 2, 0, "MODEL"],
        [20, 1, 1, 10, 1, "CLIP"]
    ],
    "groups": [],
    "config": {},
    "extra": {"ds": {"scale": 0.8, "offset": [600, 50]}},
    "version": 0.4
}

with open(f"{OUTPUT_DIR}/ui_t2i_with_lora.json", "w") as f:
    json.dump(wf, f, indent=2)
print("T2I with LoRA saved")

# I2I with LoRA - add LoadImage
import copy
wf_i2i = copy.deepcopy(wf)
wf_i2i["id"] = "i2i-lora-001"
wf_i2i["last_link_id"] = 21

load_img = {
    "id": 7, "type": "LoadImage",
    "pos": [-750, 300], "size": [260, 320],
    "flags": {}, "order": 0, "mode": 0,
    "inputs": [],
    "outputs": [
        {"name": "IMAGE", "type": "IMAGE", "links": [21]},
        {"name": "MASK", "type": "MASK", "links": None}
    ],
    "title": "Input Image",
    "properties": {"Node name for S&R": "LoadImage"},
    "widgets_values": ["example.png", "image"]
}
wf_i2i["nodes"].insert(0, load_img)

for i, n in enumerate(wf_i2i["nodes"]):
    n["order"] = i
    if n["id"] == 3:
        n["inputs"][2]["link"] = 21
        n["title"] = "Positive - Describe transformation"
        n["widgets_values"] = ["The same woman with new style, same face, same skin, photorealistic"]
    if n["type"] == "KSampler":
        n["widgets_values"] = [0, "randomize", 8, 1, "euler_ancestral", "beta", 0.65]

wf_i2i["links"].append([21, 7, 0, 3, 2, "IMAGE"])

with open(f"{OUTPUT_DIR}/ui_i2i_with_lora.json", "w") as f:
    json.dump(wf_i2i, f, indent=2)
print("I2I with LoRA saved")

print("\nLoRA workflows saved!")
