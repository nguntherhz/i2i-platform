import json
import urllib.request
import random

COMFYUI_URL = "http://localhost:8188"
WF_PATH = "/workspace/runpod-slim/ComfyUI/user/workflows/workflow_supercatalog.json"

with open(WF_PATH) as f:
    base_wf = json.load(f)

# Pick diverse scenes to test
test_scenes = [
    {"id": "CL02", "name": "coffee_shop", "prompt": "The same woman sitting at a small round cafe table outdoors, legs crossed, holding a cappuccino cup with both hands, wearing a beige knit sweater and dark skinny jeans, ankle boots, same face same eyes same skin, cozy cafe terrace with plants, morning soft light, photorealistic, full body head to toe, 8k"},
    {"id": "BS01", "name": "beach_walk", "prompt": "The same woman walking along the beach shoreline, water touching her bare feet, wearing a flowing white beach cover-up over a turquoise bikini, carrying sandals in one hand, same face same eyes same skin, golden sunset light, waves and wet sand reflections, photorealistic, full body head to toe, 8k"},
    {"id": "SA01", "name": "yoga", "prompt": "The same woman doing a warrior II yoga pose on a yoga mat in a serene garden, wearing black yoga leggings and a sage green sports bra, barefoot, focused calm expression, same face same eyes same skin, lush green garden with morning dew, soft natural light, photorealistic, full body head to toe, 8k"},
    {"id": "SA02", "name": "rollers", "prompt": "The same woman roller skating on a boardwalk promenade, dynamic movement mid-stride, wearing high-waist denim shorts and a cropped pastel pink hoodie, white inline roller skates, same face same eyes same skin, palm-lined beachfront promenade, sunny day, motion and energy, photorealistic, full body head to toe, 8k"},
    {"id": "CA02", "name": "back_view_dress", "prompt": "The same woman photographed from behind, looking over her right shoulder at camera, wearing a backless emerald green dress, heels, hair swept to one side, same face same eyes same skin, elegant marble staircase background, warm ambient lighting, photorealistic, full body head to toe, 8k"},
    {"id": "EE01", "name": "restaurant", "prompt": "The same woman sitting at an elegant restaurant table, one arm resting on table, holding wine glass, wearing a black off-shoulder cocktail dress, delicate gold jewelry, hair styled up, same face same eyes same skin, candlelit restaurant with warm ambient lighting, bokeh background, photorealistic, full body head to toe, 8k"},
]

for s in test_scenes:
    wf = json.loads(json.dumps(base_wf))
    wf["7"]["inputs"]["image"] = "mia_urban.png"
    wf["3"]["inputs"]["prompt"] = s["prompt"]
    wf["2"]["inputs"]["seed"] = random.randint(1, 999999999)
    wf["6"]["inputs"]["filename_prefix"] = f"catalog_{s['name']}"

    payload = json.dumps({"prompt": wf, "client_id": f"cat-{s['id']}"}).encode()
    req = urllib.request.Request(f"{COMFYUI_URL}/api/prompt", data=payload, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode())
    print(f"{s['id']} {s['name']}: {result['prompt_id']}")
