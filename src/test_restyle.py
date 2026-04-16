import json
import urllib.request
import random

COMFYUI_URL = "http://localhost:8188"
WF_PATH = "/workspace/runpod-slim/ComfyUI/user/workflows/workflow_restyle.json"

with open(WF_PATH) as f:
    wf = json.load(f)

tests = [
    {
        "name": "urban_to_beach",
        "prompt": "The same woman but at a beautiful tropical beach, wearing a light blue bikini top and white flowing sarong wrap skirt, barefoot on white sand, turquoise ocean and palm trees in background, same face, same eyes, same skin tone, sun-kissed glow, wind in hair, photorealistic, extremely detailed skin texture, full body head to toe, professional swimwear photography"
    },
    {
        "name": "slim_to_curvy",
        "prompt": "The same woman but with a curvier fuller body, wider hips, thicker thighs, same face, same blonde hair, wearing the same white cropped top and denim shorts, same European street background, same pose, photorealistic, extremely detailed skin texture, natural body proportions, full body head to toe"
    }
]

for t in tests:
    w = json.loads(json.dumps(wf))
    w["7"]["inputs"]["image"] = "mia_urban.png"
    w["3"]["inputs"]["prompt"] = t["prompt"]
    w["2"]["inputs"]["seed"] = random.randint(1, 999999999)
    w["6"]["inputs"]["filename_prefix"] = f"restyle_{t['name']}"

    payload = json.dumps({"prompt": w, "client_id": f"restyle-{t['name']}"}).encode()
    req = urllib.request.Request(f"{COMFYUI_URL}/api/prompt", data=payload, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode())
    print(f"{t['name']}: {result['prompt_id']}")
