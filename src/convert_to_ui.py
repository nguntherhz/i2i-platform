"""
Converts API-format ComfyUI workflows to UI-format workflows.
API format: {"1": {"class_type": "...", "inputs": {...}}}
UI format: {"nodes": [...], "links": [...], ...}
"""
import json
import sys
import uuid
import os

def convert_api_to_ui(api_workflow, title="Converted Workflow"):
    nodes = []
    links = []
    link_id = 1

    # Track output connections: (source_node_id, output_index) -> link_id
    output_links = {}

    # First pass: create nodes with positions
    node_ids = sorted(api_workflow.keys(), key=lambda x: x if not x.isdigit() else x.zfill(5))

    col = 0
    row = 0
    max_per_col = 3

    for idx, node_id in enumerate(node_ids):
        node_data = api_workflow[node_id]
        class_type = node_data["class_type"]
        inputs = node_data.get("inputs", {})
        meta = node_data.get("_meta", {})

        # Position nodes in a grid
        col = idx // max_per_col
        row = idx % max_per_col
        x = col * 400
        y = row * 300

        # Separate widget values from input connections
        widget_values = []
        input_connections = []

        for key, value in inputs.items():
            if isinstance(value, list) and len(value) == 2 and isinstance(value[1], int):
                # This is a connection reference [node_id, output_index]
                input_connections.append({"name": key, "source": value})
            else:
                widget_values.append(value)

        node = {
            "id": int(node_id) if node_id.isdigit() else idx + 100,
            "type": class_type,
            "pos": [x, y],
            "size": [350, 150],
            "flags": {},
            "order": idx,
            "mode": 0,
            "inputs": [],
            "outputs": [],
            "properties": {"Node name for S&R": class_type},
            "widgets_values": widget_values
        }

        if meta.get("title"):
            node["title"] = meta["title"]

        nodes.append(node)

    # Build a map of node_id -> node index
    node_id_map = {}
    for n in nodes:
        for nid in node_ids:
            nid_int = int(nid) if nid.isdigit() else None
            if nid_int == n["id"]:
                node_id_map[nid] = n

    # Second pass: create links and input/output slots
    for node_id in node_ids:
        node_data = api_workflow[node_id]
        inputs = node_data.get("inputs", {})
        class_type = node_data["class_type"]

        target_node = node_id_map.get(node_id)
        if not target_node:
            continue

        input_idx = 0
        for key, value in inputs.items():
            if isinstance(value, list) and len(value) == 2 and isinstance(value[1], int):
                source_node_id_str = str(value[0])
                source_output_idx = value[1]

                source_node = node_id_map.get(source_node_id_str)
                if not source_node:
                    continue

                # Determine type based on common patterns
                type_name = guess_type(key, class_type)

                # Ensure source has enough output slots
                while len(source_node["outputs"]) <= source_output_idx:
                    out_type = guess_output_type(source_node["type"], len(source_node["outputs"]))
                    source_node["outputs"].append({
                        "name": out_type,
                        "type": out_type,
                        "links": []
                    })

                # Add input slot to target
                target_node["inputs"].append({
                    "name": key,
                    "type": type_name,
                    "link": link_id
                })

                # Add link reference to source output
                source_node["outputs"][source_output_idx]["links"].append(link_id)

                # Create link: [link_id, source_node_id, source_output_idx, target_node_id, target_input_idx, type]
                links.append([
                    link_id,
                    source_node["id"],
                    source_output_idx,
                    target_node["id"],
                    input_idx,
                    type_name
                ])

                link_id += 1
                input_idx += 1

    # Build final UI workflow
    ui_workflow = {
        "id": str(uuid.uuid4()),
        "revision": 0,
        "last_node_id": max(n["id"] for n in nodes) if nodes else 0,
        "last_link_id": link_id - 1,
        "nodes": nodes,
        "links": links,
        "groups": [],
        "config": {},
        "extra": {
            "ds": {
                "scale": 0.8,
                "offset": [100, 100]
            }
        },
        "version": 0.4
    }

    return ui_workflow


def guess_type(input_name, class_type):
    """Guess the connection type based on input name."""
    name = input_name.lower()
    if name in ("model",):
        return "MODEL"
    if name in ("clip", "clip_vision"):
        return "CLIP" if "vision" not in name else "CLIP_VISION"
    if name in ("clip_vision_output",):
        return "CLIP_VISION_OUTPUT"
    if name in ("vae",):
        return "VAE"
    if name in ("positive", "negative"):
        return "CONDITIONING"
    if name in ("latent_image", "samples", "latent"):
        return "LATENT"
    if name in ("image", "images", "image1", "image2", "image3", "start_image"):
        return "IMAGE"
    if name in ("mask",):
        return "MASK"
    return "CONDITIONING"


def guess_output_type(class_type, index):
    """Guess output type based on node class and output index."""
    outputs_map = {
        "CheckpointLoaderSimple": ["MODEL", "CLIP", "VAE"],
        "LoraLoader": ["MODEL", "CLIP"],
        "CLIPTextEncode": ["CONDITIONING"],
        "TextEncodeQwenImageEditPlus": ["CONDITIONING"],
        "KSampler": ["LATENT"],
        "VAEDecode": ["IMAGE"],
        "VAEEncode": ["LATENT"],
        "EmptyLatentImage": ["LATENT"],
        "LoadImage": ["IMAGE", "MASK"],
        "SaveImage": [],
        "PreviewImage": [],
        "CLIPVisionLoader": ["CLIP_VISION"],
        "CLIPVisionEncode": ["CLIP_VISION_OUTPUT"],
        "ModelSamplingSD3": ["MODEL"],
        "WanImageToVideo": ["CONDITIONING", "CONDITIONING", "LATENT"],
        "VHS_VideoCombine": ["VHS_FILENAMES"],
    }

    types = outputs_map.get(class_type, ["*"])
    if index < len(types):
        return types[index]
    return "*"


def main():
    if len(sys.argv) < 3:
        print("Usage: python convert_to_ui.py <input_api.json> <output_ui.json> [title]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    title = sys.argv[3] if len(sys.argv) > 3 else os.path.basename(input_path).replace(".json", "")

    with open(input_path) as f:
        api_wf = json.load(f)

    ui_wf = convert_api_to_ui(api_wf, title)

    with open(output_path, "w") as f:
        json.dump(ui_wf, f, indent=2)

    print(f"Converted {len(ui_wf['nodes'])} nodes, {len(ui_wf['links'])} links -> {output_path}")


if __name__ == "__main__":
    main()
