import json
import urllib.request
import random
import sys

COMFYUI_URL = "http://localhost:8188"
WORKFLOW_PATH = "/workspace/runpod-slim/ComfyUI/user/workflows/workflow_t2i.json"

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
    catalog_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/catalog_casual_summer.json"
    max_models = int(sys.argv[2]) if len(sys.argv) > 2 else 4

    with open(WORKFLOW_PATH) as f:
        base_wf = json.load(f)

    with open(catalog_path) as f:
        catalog = json.load(f)

    models = catalog["models"][:max_models]
    neg_prompt = catalog.get("negative_prompt_default", "")

    for m in models:
        wf = json.loads(json.dumps(base_wf))
        wf["3"]["inputs"]["prompt"] = m["prompt"]
        wf["4"]["inputs"]["prompt"] = neg_prompt
        wf["2"]["inputs"]["seed"] = random.randint(1, 999999999)
        wf["6"]["inputs"]["filename_prefix"] = f"test_{m['id']}"

        result = queue_prompt(wf, f"gen-{m['id']}")
        print(f"{m['id']} ({m['name']}): queued {result['prompt_id']}")

if __name__ == "__main__":
    main()
