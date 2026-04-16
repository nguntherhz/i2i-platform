# Text-to-Image (T2I) Workflow

Genera personas ficticias fotorrealistas a partir de un prompt de texto. No requiere imagen de entrada.

## Archivo
- `workflow_t2i.json` — Workflow en formato API de ComfyUI
- `catalog.json` — Catálogo de modelos con prompts predefinidos

## Modelo
- **Checkpoint:** Qwen-Rapid-AIO-NSFW-v18.1.safetensors (28.4GB)
- **VAE:** ae.safetensors (Flux VAE, 335MB)

## Parámetros
| Parámetro | Valor |
|-----------|-------|
| Steps | 6 |
| CFG | 1.0 |
| Sampler | euler_ancestral |
| Scheduler | beta |
| Denoise | 1.0 |
| Resolution | 768 x 1024 (vertical) |

## Nodos del flujo
```
TextEncodeQwenImageEditPlus (positive prompt)
TextEncodeQwenImageEditPlus (negative prompt, sin imagen)
    ↓
CheckpointLoaderSimple → KSampler (6 steps)
    ↓
EmptyLatentImage (768x1024) → VAEDecode → SaveImage
```

## Uso via API
```bash
curl -X POST http://localhost:8188/api/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": <contenido de workflow_t2i.json>, "client_id": "mi-cliente"}'
```

Reemplazar `POSITIVE_PROMPT_HERE` en el JSON con el prompt deseado antes de enviar.

## Prompt negativo por defecto
```
deformed, watermark, low quality, bad anatomy, flat skin, plastic skin, blurry, artifacts, grid lines, ugly, disfigured, cropped, cut off legs, cut off feet, missing limbs, extra fingers, logo text, brand name visible
```

## Tips para mejores resultados
- Incluir "full body portrait" y "full body visible head to toe" para cuerpo completo
- Agregar "photorealistic, extremely detailed skin texture, raw photo, 8k resolution" para calidad
- Especificar iluminación: "golden hour", "soft afternoon sunlight", "overcast daylight"
- Ser específico con ropa, pose, escenario y tipo de cuerpo
- Seed aleatoria para variedad; seed fija para reproducir resultados exactos

## Rendimiento
- Primera ejecución: ~75s (carga del modelo en VRAM)
- Ejecuciones siguientes: ~4-5s por imagen
- GPU: RTX 5090 (32GB VRAM)
