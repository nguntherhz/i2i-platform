# i2i Platform - Referencia Rápida

## Repositorio
- **GitHub:** https://github.com/nguntherhz/i2i-platform.git
- **Remote:** origin

## SSH
- **Clave pública:** `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICB0IBpWoiROzmj+ItUru1U0KnSstYvgUzEJkOKA8sKl nicolas.gunther@hyperz.tech`
- **Clave SSH:** `~/.ssh/runpod_ed25519` (sin passphrase)

## RunPod
- **IP:** 213.173.111.157
- **Puerto SSH:** 10127
- **Usuario:** root
- **GPU:** NVIDIA GeForce RTX 5090 (32GB VRAM)
- **OS:** Ubuntu Linux 6.8.0
- **CUDA:** 13.0 | Driver: 580.126.20
- **Python:** 3.12.3
- **PyTorch:** 2.11.0+cu130
- **ComfyUI:** puerto 8188
- **ComfyUI URL:** https://t3a5h65dejiqek-8188.proxy.runpod.net/
- **JupyterLab:** puerto 8888

## Comandos útiles
```bash
# Conectar por SSH a RunPod
ssh -o IdentitiesOnly=yes -i ~/.ssh/runpod_ed25519 -p 10127 root@213.173.111.157
```

## Rutas en el Pod
- **ComfyUI root:** `/workspace/runpod-slim/ComfyUI`
- **Modelos difusión:** `/workspace/runpod-slim/ComfyUI/models/diffusion_models/`
- **VAE:** `/workspace/runpod-slim/ComfyUI/models/vae/`
- **LoRAs:** `/workspace/runpod-slim/ComfyUI/models/loras/`
- **Custom nodes:** `/workspace/runpod-slim/ComfyUI/custom_nodes/`
- **Workflows:** `/workspace/runpod-slim/ComfyUI/user/workflows/`
