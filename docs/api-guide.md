# i2i Platform - Guía de API

## Base URL
- **RunPod Proxy:** `https://t3a5h65dejiqek-8188.proxy.runpod.net`
- **Local (desde el pod):** `http://localhost:8188`

---

## Endpoints

### 1. Health Check
```
GET /api/system_stats
```
Retorna estado del sistema, versión de ComfyUI, VRAM, RAM.

---

### 2. Text-to-Image (T2I) — Generar persona ficticia

```
POST /api/prompt
Content-Type: application/json
```

```json
{
  "prompt": {
    "1": {
      "class_type": "CheckpointLoaderSimple",
      "inputs": {
        "ckpt_name": "Qwen-Rapid-AIO-NSFW-v18.1.safetensors"
      }
    },
    "3": {
      "class_type": "TextEncodeQwenImageEditPlus",
      "inputs": {
        "clip": ["1", 1],
        "vae": ["1", 2],
        "prompt": "Full body portrait, slim toned young woman, 24 years old, long wavy dark chestnut hair, honey amber eyes, warm olive skin, standing in elegant boutique hotel courtyard with white stucco walls and climbing green plants, wearing oversized cream linen blazer and matching cream linen shorts, tan strappy heeled sandals, photorealistic, extremely detailed skin texture, raw photo, 8k resolution, professional fashion campaign photography, full body visible head to toe"
      }
    },
    "4": {
      "class_type": "TextEncodeQwenImageEditPlus",
      "inputs": {
        "clip": ["1", 1],
        "vae": ["1", 2],
        "prompt": "deformed, watermark, low quality, bad anatomy, flat skin, plastic skin, blurry, artifacts, ugly, disfigured, cropped, cut off legs"
      }
    },
    "9": {
      "class_type": "EmptyLatentImage",
      "inputs": {
        "width": 768,
        "height": 1024,
        "batch_size": 1
      }
    },
    "2": {
      "class_type": "KSampler",
      "inputs": {
        "model": ["1", 0],
        "positive": ["3", 0],
        "negative": ["4", 0],
        "latent_image": ["9", 0],
        "seed": 12345,
        "steps": 6,
        "cfg": 1.0,
        "sampler_name": "euler_ancestral",
        "scheduler": "beta",
        "denoise": 1.0
      }
    },
    "5": {
      "class_type": "VAEDecode",
      "inputs": {
        "samples": ["2", 0],
        "vae": ["1", 2]
      }
    },
    "6": {
      "class_type": "SaveImage",
      "inputs": {
        "images": ["5", 0],
        "filename_prefix": "api_t2i"
      }
    }
  }
}
```

**Respuesta:**
```json
{
  "prompt_id": "abc123-...",
  "number": 1,
  "node_errors": {}
}
```

---

### 3. Obtener resultado

```
GET /api/history/{prompt_id}
```

**Estructura de la respuesta:**
```json
{
  "abc123-...": {
    "status": {
      "status_str": "success",
      "completed": true
    },
    "outputs": {
      "6": {
        "images": [
          {
            "filename": "api_t2i_00001_.png",
            "subfolder": "",
            "type": "output"
          }
        ]
      }
    }
  }
}
```

---

### 4. Descargar imagen generada

```
GET /view?filename={filename}&type=output
```

Retorna el archivo binario (PNG).

---

### 5. Subir imagen (para I2I)

```
POST /upload/image
Content-Type: multipart/form-data
```

| Campo | Valor |
|-------|-------|
| image | (archivo binario) |
| type | input |
| overwrite | true |

**Respuesta:**
```json
{
  "name": "nombre_archivo.png",
  "subfolder": "",
  "type": "input"
}
```

---

### 6. Image-to-Image (I2I) — Transformar imagen existente

Primero subir imagen con el endpoint anterior, luego:

```
POST /api/prompt
Content-Type: application/json
```

```json
{
  "prompt": {
    "1": {
      "class_type": "CheckpointLoaderSimple",
      "inputs": {
        "ckpt_name": "Qwen-Rapid-AIO-NSFW-v18.1.safetensors"
      }
    },
    "7": {
      "class_type": "LoadImage",
      "inputs": {
        "image": "NOMBRE_DEL_ARCHIVO_SUBIDO.png",
        "upload": "image"
      }
    },
    "3": {
      "class_type": "TextEncodeQwenImageEditPlus",
      "inputs": {
        "clip": ["1", 1],
        "vae": ["1", 2],
        "prompt": "The same woman at a tropical beach, wearing a turquoise bikini, barefoot on white sand, same face same eyes same skin, photorealistic, full body head to toe, 8k",
        "image1": ["7", 0]
      }
    },
    "4": {
      "class_type": "TextEncodeQwenImageEditPlus",
      "inputs": {
        "clip": ["1", 1],
        "vae": ["1", 2],
        "prompt": "different face, different person, different skin color, deformed, bad anatomy, blurry, low quality, watermark, artifacts"
      }
    },
    "9": {
      "class_type": "EmptyLatentImage",
      "inputs": {
        "width": 768,
        "height": 1024,
        "batch_size": 1
      }
    },
    "2": {
      "class_type": "KSampler",
      "inputs": {
        "model": ["1", 0],
        "positive": ["3", 0],
        "negative": ["4", 0],
        "latent_image": ["9", 0],
        "seed": 0,
        "steps": 8,
        "cfg": 1.0,
        "sampler_name": "euler_ancestral",
        "scheduler": "beta",
        "denoise": 0.72
      }
    },
    "5": {
      "class_type": "VAEDecode",
      "inputs": {
        "samples": ["2", 0],
        "vae": ["1", 2]
      }
    },
    "6": {
      "class_type": "SaveImage",
      "inputs": {
        "images": ["5", 0],
        "filename_prefix": "api_i2i"
      }
    }
  }
}
```

---

### 7. Liberar VRAM

```
POST /api/free
Content-Type: application/json
```

```json
{
  "unload_models": true,
  "free_memory": true
}
```

---

### 8. Ver cola de ejecución

```
GET /api/queue
```

---

## Parámetros ajustables

| Parámetro | Nodo | Campo | Rango | Descripción |
|-----------|------|-------|-------|-------------|
| Prompt positivo | "3" | `prompt` | texto | Lo que querés generar |
| Prompt negativo | "4" | `prompt` | texto | Lo que querés evitar |
| Seed | "2" | `seed` | 0-999999999 | 0 = random, fijo = reproducible |
| Steps | "2" | `steps` | 4-8 | Más = más calidad, más lento |
| Denoise | "2" | `denoise` | 0.0-1.0 | Solo I2I. Más alto = más cambio |
| Ancho | "9" | `width` | 512-1024 | Múltiplos de 64 |
| Alto | "9" | `height` | 512-1024 | Múltiplos de 64 |
| Prefijo salida | "6" | `filename_prefix` | texto | Prefijo del archivo de salida |
| Imagen input | "7" | `image` | nombre archivo | Solo I2I. Nombre del archivo subido |

## Guía de denoise (solo I2I)

| Denoise | Uso |
|---------|-----|
| 0.35 - 0.45 | Cambios mínimos (color de pelo, tono) |
| 0.45 - 0.55 | Cambio de ropa |
| 0.55 - 0.65 | Cambio de ropa + pelo |
| 0.65 - 0.75 | Cambio de ropa + pelo + escena |
| 0.75 - 0.85 | Transformación completa (cuerpo + escena) |

## Flujo típico de uso

```
1. POST /api/prompt          → Obtener prompt_id
2. GET /api/history/{id}     → Esperar status "success"
3. GET /view?filename=...    → Descargar imagen
```

Para I2I agregar antes:
```
0. POST /upload/image        → Subir imagen, obtener nombre
```

## Tiempos estimados (RTX 5090)

| Operación | Primera vez | Siguientes |
|-----------|------------|------------|
| T2I (6 steps) | ~75s (carga modelo) | ~4-5s |
| I2I (8 steps) | ~75s (carga modelo) | ~5-6s |
| I2V (4 steps, 81 frames) | ~120s (carga modelo) | ~30-40s |

## Notas
- El modelo se carga en VRAM la primera vez y queda en cache
- Si se cambia de workflow (T2I → I2V), el modelo anterior se descarga y el nuevo se carga
- Usar `POST /api/free` para liberar VRAM manualmente si es necesario
- El watcher reinicia ComfyUI automáticamente si se cae
