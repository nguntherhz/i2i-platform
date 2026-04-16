# i2i Setup Log

## Etapa 1: Preparación del Terreno (2026-04-16)
- [x] Verificación GPU: RTX 5090, Driver 580.126.20, CUDA 13.0
- [x] Directorio persistente: `/workspace/runpod-slim/ComfyUI`
- [x] pip actualizado a 26.0.1
- [x] PyTorch 2.11.0+cu130 verificado con CUDA

## Etapa 2: El Músculo - Descarga de Modelos (2026-04-16)
- [x] **Qwen NSFW v18.1** (28.4GB) → `diffusion_models/Qwen-Rapid-AIO-NSFW-v18.1.safetensors`
  - Fuente: `huggingface.co/Phr00t/Qwen-Image-Edit-Rapid-AIO/resolve/main/v18/`
  - Nota: v5 original no existía (404). Se usó la última versión v18.1
- [x] **Flux VAE** (335MB) → `vae/ae.safetensors`
  - Fuente: `huggingface.co/cocktailpeanut/xulf-dev` (mirror público)
  - Nota: repo oficial (black-forest-labs/FLUX.1-dev) requiere token HF
- [x] **F2P LoRA** (451MB) → `loras/Qwen-Image-Edit-F2P.safetensors`
  - Fuente: `huggingface.co/DiffSynth-Studio/Qwen-Image-Edit-F2P` (edit_0928_lora_step40000)
  - Nota: URL original de Phr00t daba 404. Encontrado via CivitAI → ModelScope → HuggingFace
  - Autor original: DiffSynth-Studio. Strength recomendado: 0.6-0.8

## Etapa 3: El Cerebro - Nodos y Workflow (2026-04-16)
- [x] **ComfyUI-Forbidden-Vision** clonado + dependencias instaladas
  - `custom_nodes/ComfyUI-Forbidden-Vision/`
  - Deps: ultralytics, timm, segmentation-models-pytorch, scikit-image, polars
- [x] **Workflow JSON** descargado → `user/workflows/Qwen-Rapid-AIO.json`
- [x] **Qwen Node v2** (Phr00t fix) → `nodes_qwen_v2.py` en raíz ComfyUI
  - Corrige problemas de scaling/cropping, soporta hasta 4 imágenes input
- [x] **ComfyUI reiniciado** - todos los nodos cargaron correctamente
  - Forbidden Vision: 14.3s de carga (OK)

## Nodos custom instalados en el pod
- ComfyUI-Manager
- ComfyUI-Forbidden-Vision
- ComfyUI-KJNodes
- ComfyUI-RunpodDirect
- Civicomfy

## Parámetros recomendados (Phr00t README)
- **Steps:** 4-8
- **CFG:** 1.0
- **Scheduler:** euler_ancestral/beta (recomendado para v18)
- **Precision:** FP8

## Etapa 4: Configuración del Workflow (2026-04-16)
- [x] Workflow JSON actualizado:
  - Checkpoint: `Qwen-Rapid-AIO-NSFW-v18.1.safetensors` (era v1)
  - KSampler: steps=6, CFG=1.0, euler_ancestral/beta, denoise=1
- [x] Todos los nodos verificados via API (0 faltantes):
  - CheckpointLoaderSimple, KSampler, VAEDecode, PreviewImage,
    EmptyLatentImage, TextEncodeQwenImageEditPlus, LoadImage
- [x] Nodo Qwen v2 (Phr00t fix) disponible en `nodes_qwen_v2.py`
- [ ] Forbidden Vision: pendiente conectar post-procesado en workflow
- [ ] F2P LoRA: no disponible, buscar alternativa

## Pendientes
- [x] F2P LoRA descargado y detectado por ComfyUI
- [ ] Agregar nodos Forbidden Vision al workflow (post-procesado rostros)
- [ ] Probar workflow completo con imagen de test
- [ ] Ajustar denoise strength según caso de uso (0.45-0.55 moderado, 0.65-0.75 profundo)
