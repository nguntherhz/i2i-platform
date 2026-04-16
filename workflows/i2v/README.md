# Image-to-Video (I2V) Workflow

Genera videos de 3-5 segundos a partir de una imagen estática y un prompt de acción.

## Archivos
- `workflow_i2v.json` — Workflow en formato API de ComfyUI
- `video_scripts.json` — 10 guiones predefinidos de transiciones y acciones

## Modelo
- **Checkpoint:** wan2.2-i2v-rapid-aio.safetensors (23.4GB) — Wan 2.2 I2V de Phr00t
- **CLIP Vision:** clip-vision_vit-h.safetensors
- **Ubicación:** `models/diffusion_models/` (no checkpoints)

## Parámetros
| Parámetro | Valor |
|-----------|-------|
| Resolution | 640 x 640 |
| Frames | 81 |
| FPS | 24 |
| Duration | ~3.4 segundos |
| Steps | 4 |
| CFG | 1.0 |
| Sampler | sa_solver |
| Scheduler | beta |
| Shift | 8.0 (ModelSamplingSD3) |

## Nodos del flujo
```
LoadImage → CLIPVisionEncode ──┐
                                ├── WanImageToVideo → KSampler → VAEDecode → VHS_VideoCombine (.mp4)
CLIPTextEncode (prompt) ───────┘
CheckpointLoader → ModelSamplingSD3 (shift=8)
```

## Categorías de guiones disponibles
1. **Lifestyle transition** — Cambio de escena/contexto (oficina → casa)
2. **Scene transition** — Transición de fondo (playa → ciudad)
3. **Outfit transition** — Cambio de ropa (sport → sleepwear)
4. **Pose transition** — Cambio de pose (parada → sentada → acostada)
5. **Dynamic action** — Acciones en movimiento (caminar, yoga)
6. **Beauty moment** — Momento editorial (hair flip, sonrisa)
7. **Scene action** — Acción en escena (entrar a piscina)
8. **Lifestyle moment** — Momento cotidiano (tomar café)

## Uso via API
```bash
# 1. Subir imagen
curl -X POST http://localhost:8188/upload/image -F "image=@modelo.png" -F "type=input"

# 2. Ejecutar (reemplazar INPUT_IMAGE y VIDEO_PROMPT_HERE)
curl -X POST http://localhost:8188/api/prompt -H "Content-Type: application/json" -d '{"prompt": <workflow_json>}'

# 3. El video se guarda como .mp4 en output/
```

## Notas
- El modelo Wan I2V (23.4GB) y Qwen (27GB) no caben juntos en VRAM. ComfyUI los intercambia automáticamente.
- La primera ejecución de video tarda más (carga del modelo). Las siguientes son más rápidas.
- Para videos más largos, aumentar `length` (frames). 81 frames = 3.4s, 161 frames = 6.7s.
- El prompt describe la **acción/movimiento**, no la apariencia estática (esa viene de la imagen).
