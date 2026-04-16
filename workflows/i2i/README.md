# Image-to-Image (I2I) Workflow

Edita una imagen existente mediante un prompt de texto. Recibe una imagen de entrada y genera una versión modificada.

## Archivo
- `workflow_api.json` — Workflow en formato API de ComfyUI

## Modelo
- **Checkpoint:** Qwen-Rapid-AIO-NSFW-v18.1.safetensors (28.4GB)
- **VAE:** ae.safetensors (Flux VAE, 335MB)

## Parámetros
| Parámetro | Valor | Notas |
|-----------|-------|-------|
| Steps | 6 | Suficiente para RTX 5090 |
| CFG | 1.0 | Mantener en 1.0 para respetar la imagen original |
| Sampler | euler_ancestral | Recomendado por Phr00t para v18 |
| Scheduler | beta | Recomendado por Phr00t para v18 |
| Denoise | 0.65 | 0.45-0.55 cambio moderado, 0.65-0.75 cambio profundo |
| Resolution | 768 x 1024 (vertical) | Ajustable según imagen de entrada |

## Nodos del flujo
```
LoadImage (imagen de entrada)
    ↓
TextEncodeQwenImageEditPlus (positive prompt + imagen)
TextEncodeQwenImageEditPlus (negative prompt, sin imagen)
    ↓
CheckpointLoaderSimple → KSampler (6 steps, denoise 0.65)
    ↓
EmptyLatentImage (768x1024) → VAEDecode → SaveImage
```

## Uso via API

### 1. Subir imagen
```bash
curl -X POST http://localhost:8188/upload/image \
  -F "image=@mi_imagen.png" \
  -F "type=input"
```

### 2. Ejecutar workflow
Reemplazar `INPUT_IMAGE` en el JSON con el nombre del archivo subido, luego:
```bash
curl -X POST http://localhost:8188/api/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": <contenido de workflow_api.json>, "client_id": "mi-cliente"}'
```

### 3. Obtener resultado
```bash
curl http://localhost:8188/api/history/<prompt_id>
curl http://localhost:8188/view?filename=<output_filename>&type=output
```

## Guía de denoise
- **0.45 - 0.55:** Cambios sutiles (ajuste de color, iluminación, detalles menores)
- **0.55 - 0.65:** Cambios moderados (modificar ropa, accesorios)
- **0.65 - 0.75:** Cambios profundos (transformaciones estructurales)

## Rendimiento
- Primera ejecución: ~75s (carga del modelo en VRAM)
- Ejecuciones siguientes: ~4-5s por imagen
- GPU: RTX 5090 (32GB VRAM)
