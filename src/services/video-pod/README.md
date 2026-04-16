# Video Pod Setup

## Requisitos
- RunPod template: ComfyUI CUDA 13
- GPU: RTX 5090 32GB (o RTX 4090 24GB mínimo)
- Disco: 50GB+ (modelo 22GB + deps)

## Setup rápido

1. Crear pod en RunPod con template ComfyUI CUDA 13
2. Obtener SSH: `ssh root@IP -p PORT -i ~/.ssh/runpod_ed25519`
3. Subir y ejecutar setup:

```bash
# Desde tu PC
scp -i ~/.ssh/runpod_ed25519 -P PORT setup.sh root@IP:/tmp/
ssh -i ~/.ssh/runpod_ed25519 -p PORT root@IP "bash /tmp/setup.sh"
```

4. Esperar ~5 min (descarga modelo 22GB)
5. Verificar: `curl http://localhost:8188/api/system_stats`

## Lo que instala
- VideoHelperSuite (custom node para combinar frames a mp4)
- Wan 2.2 I2V Rapid AIO (22GB) en checkpoints
- CLIP Vision para Wan
- Workflow de ejemplo
- Watcher con auto-restart

## Después del setup
- Actualizar `BASE_URL_VIDEO` en el engine con la URL del proxy de RunPod
- Testear con: `POST /api/prompt` usando el workflow I2V

## Modelo
- **Wan 2.2 14B Rapid AllInOne** por Phr00t
- Image-to-Video: 81 frames, 640x640, 24fps = ~3.4s
- 4 steps con sa_solver/beta, CFG 1.0
- Tiempo: ~30-40s por video (después de cargar modelo)
