import json
import copy

OUTPUT_DIR = "/workspace/runpod-slim/ComfyUI/user/default/workflows"

# Base T2I workflow in proper UI format
base_t2i = {
    "id": "t2i-workflow-001",
    "revision": 0,
    "last_node_id": 9,
    "last_link_id": 11,
    "nodes": [
        {
            "id": 1, "type": "CheckpointLoaderSimple",
            "pos": [-250, 30], "size": [370, 100],
            "flags": {}, "order": 0, "mode": 0,
            "inputs": [],
            "outputs": [
                {"name": "MODEL", "type": "MODEL", "links": [1]},
                {"name": "CLIP", "type": "CLIP", "links": [2, 4]},
                {"name": "VAE", "type": "VAE", "links": [5, 6, 7]}
            ],
            "properties": {"Node name for S&R": "CheckpointLoaderSimple"},
            "widgets_values": ["Qwen-Rapid-AIO-NSFW-v18.1.safetensors"]
        },
        {
            "id": 3, "type": "TextEncodeQwenImageEditPlus",
            "pos": [-230, 180], "size": [380, 200],
            "flags": {}, "order": 1, "mode": 0,
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
            "widgets_values": ["Full body portrait, beautiful young woman, 25 years old, photorealistic, 8k resolution"]
        },
        {
            "id": 4, "type": "TextEncodeQwenImageEditPlus",
            "pos": [-230, 430], "size": [380, 200],
            "flags": {}, "order": 2, "mode": 0,
            "inputs": [
                {"name": "clip", "type": "CLIP", "link": 4},
                {"name": "vae", "type": "VAE", "link": 7, "shape": 7},
                {"name": "image1", "type": "IMAGE", "link": None, "shape": 7},
                {"name": "image2", "type": "IMAGE", "link": None, "shape": 7},
                {"name": "image3", "type": "IMAGE", "link": None, "shape": 7}
            ],
            "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [8]}],
            "title": "Negative Prompt (leave blank or minimal)",
            "properties": {"Node name for S&R": "TextEncodeQwenImageEditPlus"},
            "widgets_values": ["deformed, watermark, low quality, bad anatomy, blurry, ugly, disfigured"]
        },
        {
            "id": 9, "type": "EmptyLatentImage",
            "pos": [-200, 680], "size": [270, 106],
            "flags": {}, "order": 3, "mode": 0,
            "inputs": [],
            "outputs": [{"name": "LATENT", "type": "LATENT", "links": [9]}],
            "title": "Output Size",
            "properties": {"Node name for S&R": "EmptyLatentImage"},
            "widgets_values": [768, 1024, 1]
        },
        {
            "id": 2, "type": "KSampler",
            "pos": [200, 30], "size": [270, 262],
            "flags": {}, "order": 4, "mode": 0,
            "inputs": [
                {"name": "model", "type": "MODEL", "link": 1},
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
            "pos": [520, 30], "size": [140, 46],
            "flags": {}, "order": 5, "mode": 0,
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
            "pos": [520, 130], "size": [300, 350],
            "flags": {}, "order": 6, "mode": 0,
            "inputs": [{"name": "images", "type": "IMAGE", "link": 11}],
            "outputs": [],
            "properties": {"Node name for S&R": "PreviewImage"},
            "widgets_values": []
        }
    ],
    "links": [
        [1, 1, 0, 2, 0, "MODEL"],
        [2, 1, 1, 3, 0, "CLIP"],
        [3, 3, 0, 2, 1, "CONDITIONING"],
        [4, 1, 1, 4, 0, "CLIP"],
        [5, 1, 2, 3, 1, "VAE"],
        [6, 1, 2, 5, 1, "VAE"],
        [7, 1, 2, 4, 1, "VAE"],
        [8, 4, 0, 2, 2, "CONDITIONING"],
        [9, 9, 0, 2, 3, "LATENT"],
        [10, 2, 0, 5, 0, "LATENT"],
        [11, 5, 0, 6, 0, "IMAGE"]
    ],
    "groups": [],
    "config": {},
    "extra": {"ds": {"scale": 0.9, "offset": [500, 50]}},
    "version": 0.4
}

# Save T2I
with open(f"{OUTPUT_DIR}/ui_t2i.json", "w") as f:
    json.dump(base_t2i, f, indent=2)
print("T2I saved")

# I2I base - add LoadImage node connected to positive prompt image1
def make_i2i(wf_id, title_pos, title_neg, pos_prompt, neg_prompt, denoise, steps, filename):
    wf = copy.deepcopy(base_t2i)
    wf["id"] = wf_id
    wf["last_node_id"] = 9
    wf["last_link_id"] = 12

    # Add LoadImage
    load_img = {
        "id": 7, "type": "LoadImage",
        "pos": [-620, 200], "size": [260, 320],
        "flags": {}, "order": 0, "mode": 0,
        "inputs": [],
        "outputs": [
            {"name": "IMAGE", "type": "IMAGE", "links": [12]},
            {"name": "MASK", "type": "MASK", "links": None}
        ],
        "title": "Input Image",
        "properties": {"Node name for S&R": "LoadImage"},
        "widgets_values": ["example.png", "image"]
    }
    wf["nodes"].insert(0, load_img)

    # Fix order numbers
    for i, n in enumerate(wf["nodes"]):
        n["order"] = i

    # Connect image1 on positive prompt node
    for n in wf["nodes"]:
        if n["id"] == 3:
            n["inputs"][2]["link"] = 12  # image1
            n["title"] = title_pos
            n["widgets_values"] = [pos_prompt]
        if n["id"] == 4:
            n["title"] = title_neg
            n["widgets_values"] = [neg_prompt]
        if n["type"] == "KSampler":
            n["widgets_values"] = [0, "randomize", steps, 1, "euler_ancestral", "beta", denoise]

    wf["links"].append([12, 7, 0, 3, 2, "IMAGE"])

    with open(f"{OUTPUT_DIR}/{filename}", "w") as f:
        json.dump(wf, f, indent=2)
    print(f"{filename} saved")

neg_default = "different face, different person, different skin color, deformed, bad anatomy, blurry, low quality, watermark, artifacts"

make_i2i("i2i-001", "Positive - Describe transformation", "Negative - Preserve identity",
         "The same woman with new style, same face same skin, photorealistic, full body",
         neg_default, 0.72, 8, "ui_i2i.json")

make_i2i("hair-001", "Positive - Describe NEW hair", "Negative - Preserve identity",
         "The same woman with short platinum blonde pixie cut hair, same face, same outfit, same pose, same background, photorealistic",
         "different face, different person, different body, different outfit, different clothing, deformed, bad anatomy, blurry, low quality, watermark",
         0.45, 6, "ui_change_hair.json")

make_i2i("outfit-001", "Positive - Describe NEW outfit", "Negative - Preserve identity",
         "The same woman wearing a red summer dress, same face, same body, same pose, same background, photorealistic",
         neg_default, 0.55, 6, "ui_change_outfit.json")

make_i2i("restyle-001", "Positive - NEW style (body + scene + outfit)", "Negative - Preserve face",
         "The same woman at tropical beach, wearing white bikini, barefoot on sand, same face same eyes same skin, photorealistic, full body head to toe",
         "different face, different person, different eyes, different skin color, deformed, bad anatomy, blurry, low quality, watermark, artifacts, ugly",
         0.75, 8, "ui_restyle.json")

make_i2i("catalog-001", "Positive - Scene / Pose / Outfit", "Negative - Lock identity",
         "The same woman sitting at cafe terrace, legs crossed, holding cappuccino, wearing beige sweater and jeans, same face same eyes same skin, photorealistic, full body head to toe",
         "different face, different person, different eyes, different nose, different mouth, different skin color, different age, deformed, bad anatomy, blurry, low quality, watermark, artifacts, ugly",
         0.72, 8, "ui_supercatalog.json")

make_i2i("transform-001", "Positive - Full transformation (outfit + hair + scene)", "Negative - Preserve face",
         "The same woman with short black bob hair, wearing blue business suit, standing in modern office, same face, same skin, photorealistic, full body",
         "different face, different person, different skin color, deformed, bad anatomy, blurry, low quality, watermark, artifacts, ugly",
         0.65, 8, "ui_full_transform.json")

print("\nAll 7 UI workflows saved!")
