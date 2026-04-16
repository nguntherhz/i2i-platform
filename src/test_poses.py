import json
import urllib.request
import random
import sys

COMFYUI_URL = "http://localhost:8188"
WORKFLOW_PATH = "/workspace/runpod-slim/ComfyUI/user/workflows/workflow_t2i.json"

NEG = "deformed, watermark, low quality, bad anatomy, flat skin, plastic skin, blurry, artifacts, grid lines, ugly, disfigured, cropped, cut off legs, cut off feet, missing limbs, extra fingers, logo text"

# Same base person, different poses and camera angles
BASE_PERSON = "young woman, 24 years old, long wavy dark chestnut hair, honey amber eyes, warm olive skin, slim toned body"

POSES = [
    {
        "name": "front_standing",
        "prompt": f"Full body portrait, {BASE_PERSON}, standing facing camera directly, hands at sides, neutral confident pose, wearing white fitted t-shirt and blue jeans, white sneakers, clean studio white background, front view, straight on camera angle, photorealistic, extremely detailed skin texture, raw photo, 8k, professional fashion photography, full body visible head to toe"
    },
    {
        "name": "back_view",
        "prompt": f"Full body portrait from behind, {BASE_PERSON}, standing with back to camera, looking over left shoulder at camera, wearing white fitted t-shirt and blue jeans, white sneakers, clean studio white background, rear view, back facing camera, photorealistic, extremely detailed skin texture, raw photo, 8k, professional fashion photography, full body visible head to toe"
    },
    {
        "name": "side_profile",
        "prompt": f"Full body portrait, {BASE_PERSON}, standing in side profile view, facing left, arms relaxed, wearing white fitted t-shirt and blue jeans, white sneakers, clean studio white background, side view, 90 degree angle from camera, photorealistic, extremely detailed skin texture, raw photo, 8k, professional fashion photography, full body visible head to toe"
    },
    {
        "name": "three_quarter",
        "prompt": f"Full body portrait, {BASE_PERSON}, standing at three-quarter angle facing slightly left, one hand on hip, wearing white fitted t-shirt and blue jeans, white sneakers, clean studio white background, three quarter view, 45 degree angle, photorealistic, extremely detailed skin texture, raw photo, 8k, professional fashion photography, full body visible head to toe"
    },
    {
        "name": "sitting",
        "prompt": f"Full body portrait, {BASE_PERSON}, sitting on high stool, legs crossed, hands on knee, wearing white fitted t-shirt and blue jeans, white sneakers, clean studio white background, front view, slightly low camera angle, photorealistic, extremely detailed skin texture, raw photo, 8k, professional fashion photography, full body visible head to toe"
    },
    {
        "name": "walking_dynamic",
        "prompt": f"Full body portrait, {BASE_PERSON}, captured mid-stride walking towards camera, dynamic movement, hair flowing, wearing white fitted t-shirt and blue jeans, white sneakers, clean studio white background, front view, eye level camera, photorealistic, extremely detailed skin texture, raw photo, 8k, professional fashion photography, full body visible head to toe"
    },
    {
        "name": "low_angle",
        "prompt": f"Full body portrait shot from low angle looking up, {BASE_PERSON}, standing with hands on hips, powerful pose, wearing white fitted t-shirt and blue jeans, white sneakers, clean studio white background, low angle camera looking upward, worm eye view, photorealistic, extremely detailed skin texture, raw photo, 8k, professional fashion photography, full body visible head to toe"
    },
    {
        "name": "high_angle",
        "prompt": f"Full body portrait shot from high angle looking down, {BASE_PERSON}, standing looking up at camera, natural relaxed pose, wearing white fitted t-shirt and blue jeans, white sneakers, clean studio white background, high angle camera looking downward, bird eye view, photorealistic, extremely detailed skin texture, raw photo, 8k, professional fashion photography, full body visible head to toe"
    }
]

def queue_prompt(workflow, client_id):
    payload = json.dumps({"prompt": workflow, "client_id": client_id}).encode()
    req = urllib.request.Request(
        f"{COMFYUI_URL}/api/prompt",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read().decode())

def main():
    with open(WORKFLOW_PATH) as f:
        base_wf = json.load(f)

    for p in POSES:
        wf = json.loads(json.dumps(base_wf))
        wf["3"]["inputs"]["prompt"] = p["prompt"]
        wf["4"]["inputs"]["prompt"] = NEG
        wf["2"]["inputs"]["seed"] = random.randint(1, 999999999)
        wf["6"]["inputs"]["filename_prefix"] = f"pose_{p['name']}"

        result = queue_prompt(wf, f"pose-{p['name']}")
        print(f"{p['name']}: {result['prompt_id']}")

if __name__ == "__main__":
    main()
