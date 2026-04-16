# i2i Platform - Guía de Integración Completa

## Resumen

La plataforma i2i expone una API HTTP sobre ComfyUI para generar y transformar imágenes de personas ficticias. Soporta dos flujos principales:

- **T2I (Text-to-Image):** Genera personas desde un prompt de texto
- **I2I (Image-to-Image):** Transforma una imagen existente con un prompt

Ambos flujos soportan **LoRAs opcionales** por categoría para modificar el comportamiento del modelo.

---

## Conexión

| Variable | Valor |
|----------|-------|
| Base URL | `https://t3a5h65dejiqek-8188.proxy.runpod.net` |
| Protocolo | HTTPS |
| CORS | Habilitado |
| Auth | Sin autenticación (acceso por URL obscura) |

---

## Endpoints

| Endpoint | Método | Content-Type | Descripción |
|----------|--------|-------------|-------------|
| `/api/system_stats` | GET | - | Health check |
| `/api/prompt` | POST | application/json | Ejecutar workflow |
| `/api/history/{prompt_id}` | GET | - | Obtener resultado |
| `/view?filename={name}&type=output` | GET | - | Descargar imagen |
| `/upload/image` | POST | multipart/form-data | Subir imagen (solo I2I) |
| `/api/free` | POST | application/json | Liberar VRAM |
| `/api/queue` | GET | - | Ver cola de ejecución |

---

## Modelo de Datos: Template

Cada template sigue esta estructura:

```json
{
  "id": "t2i-sportswear-001",
  "metadata": {
    "title": "Sportswear Model - Running",
    "description": "Athletic woman in premium sportswear",
    "category": "Sportswear"
  },
  "category": "Sportswear",
  "workflow_type": "t2i | i2i",
  "lora": null | {
    "name": "archivo.safetensors",
    "strength_model": 0.7,
    "strength_clip": 0.7
  },
  "workflow_params": {
    "prompts": {
      "positive": "...",
      "negative": "..."
    },
    "image_config": {
      "width": 768,
      "height": 1024,
      "steps": 6,
      "cfg": 1.0,
      "denoise": 1.0,
      "sampler": "euler_ancestral",
      "scheduler": "beta"
    }
  }
}
```

---

## Sistema de LoRAs por Categoría

Las LoRAs son modificadores que se aplican al modelo base para alterar su comportamiento. Se asignan por categoría.

### Configuración de LoRAs

```json
{
  "lora_registry": {
    "face_consistency": {
      "file": "Qwen-Image-Edit-F2P.safetensors",
      "strength_model": 0.7,
      "strength_clip": 0.7,
      "description": "Preserva identidad facial en transformaciones I2I"
    },
    "none": {
      "file": null,
      "description": "Sin LoRA, modelo base directo"
    }
  },

  "category_lora_map": {
    "Sportswear": "none",
    "Swimwear": "none",
    "Casual Summer": "none",
    "Intimates": "none",
    "Young Fashion": "none",
    "Accessories": "none",
    "Executive Gym": "none",
    "I2I Transform": "none",
    "I2I Super Catalog": "none",
    "I2I with LoRA": "face_consistency"
  }
}
```

### Agregar nueva LoRA

1. Descargar el `.safetensors` al pod:
   ```bash
   ssh root@IP -p PORT "cd /workspace/runpod-slim/ComfyUI/models/loras && wget -O mi_lora.safetensors 'URL'"
   ```
2. Agregar al `lora_registry`
3. Asignar categorías en `category_lora_map`

### LoRAs disponibles en HuggingFace para Qwen

| LoRA | Uso | URL |
|------|-----|-----|
| Qwen-Image-Edit-F2P | Face consistency | `DiffSynth-Studio/Qwen-Image-Edit-F2P` |
| SNOFS | NSFW enhancement | Incluido en el modelo AIO |
| InSubject | Character consistency | Incluido en el modelo AIO |

---

## Flujo de Integración

### Flujo T2I (Text-to-Image)

```
Cliente                              ComfyUI API
  |                                      |
  |  1. POST /api/prompt (JSON)          |
  |  ─────────────────────────────────>  |
  |  { prompt_id }                       |
  |  <─────────────────────────────────  |
  |                                      |
  |  2. GET /api/history/{prompt_id}     |
  |  ─────────────────────────────────>  |  (polling cada 2s)
  |  { status: "success", outputs }      |
  |  <─────────────────────────────────  |
  |                                      |
  |  3. GET /view?filename=X&type=output |
  |  ─────────────────────────────────>  |
  |  (binary PNG)                        |
  |  <─────────────────────────────────  |
```

### Flujo I2I (Image-to-Image)

```
Cliente                              ComfyUI API
  |                                      |
  |  1. POST /upload/image               |
  |  ─────────────────────────────────>  |
  |  { name: "uploaded.png" }            |
  |  <─────────────────────────────────  |
  |                                      |
  |  2. POST /api/prompt (JSON)          |
  |  ─────────────────────────────────>  |
  |  { prompt_id }                       |
  |  <─────────────────────────────────  |
  |                                      |
  |  3. GET /api/history/{prompt_id}     |
  |  ─────────────────────────────────>  |
  |  { status: "success", outputs }      |
  |  <─────────────────────────────────  |
  |                                      |
  |  4. GET /view?filename=X&type=output |
  |  ─────────────────────────────────>  |
  |  (binary PNG)                        |
  |  <─────────────────────────────────  |
```

---

## Construcción del JSON de ComfyUI

Tu engine debe construir el JSON de ComfyUI dinámicamente según el template. Hay dos variantes: con LoRA y sin LoRA.

### Pseudocódigo del Engine

```python
def build_comfyui_payload(template, input_image=None, seed=0):
    t = template
    prompts = t["workflow_params"]["prompts"]
    config = t["workflow_params"]["image_config"]
    lora = t.get("lora")
    
    # Nodo base: Checkpoint
    workflow = {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "Qwen-Rapid-AIO-NSFW-v18.1.safetensors"}
        }
    }
    
    # Si tiene LoRA, insertar nodo LoraLoader
    if lora and lora.get("name"):
        workflow["10"] = {
            "class_type": "LoraLoader",
            "inputs": {
                "model": ["1", 0],
                "clip": ["1", 1],
                "lora_name": lora["name"],
                "strength_model": lora["strength_model"],
                "strength_clip": lora["strength_clip"]
            }
        }
        model_source = "10"  # KSampler usa modelo del LoRA
        clip_source = "10"   # CLIP usa output del LoRA
    else:
        model_source = "1"
        clip_source = "1"
    
    # Prompt positivo
    node_3 = {
        "class_type": "TextEncodeQwenImageEditPlus",
        "inputs": {
            "clip": [clip_source, 1],
            "vae": ["1", 2],
            "prompt": prompts["positive"]
        }
    }
    
    # Si es I2I, agregar imagen al prompt positivo
    if t["workflow_type"] == "i2i" and input_image:
        workflow["7"] = {
            "class_type": "LoadImage",
            "inputs": {"image": input_image, "upload": "image"}
        }
        node_3["inputs"]["image1"] = ["7", 0]
    
    workflow["3"] = node_3
    
    # Prompt negativo
    workflow["4"] = {
        "class_type": "TextEncodeQwenImageEditPlus",
        "inputs": {
            "clip": [clip_source, 1],
            "vae": ["1", 2],
            "prompt": prompts["negative"]
        }
    }
    
    # Latent image (tamaño de salida)
    workflow["9"] = {
        "class_type": "EmptyLatentImage",
        "inputs": {
            "width": config["width"],
            "height": config["height"],
            "batch_size": 1
        }
    }
    
    # KSampler
    workflow["2"] = {
        "class_type": "KSampler",
        "inputs": {
            "model": [model_source, 0],
            "positive": ["3", 0],
            "negative": ["4", 0],
            "latent_image": ["9", 0],
            "seed": seed if seed > 0 else random.randint(1, 999999999),
            "steps": config["steps"],
            "cfg": config["cfg"],
            "sampler_name": config["sampler"],
            "scheduler": config["scheduler"],
            "denoise": config["denoise"]
        }
    }
    
    # Decode + Save
    workflow["5"] = {
        "class_type": "VAEDecode",
        "inputs": {"samples": ["2", 0], "vae": ["1", 2]}
    }
    workflow["6"] = {
        "class_type": "SaveImage",
        "inputs": {"images": ["5", 0], "filename_prefix": t["id"]}
    }
    
    return {"prompt": workflow}
```

---

## Ejemplos HTTP Completos

### T2I - Generar persona

```http
POST /api/prompt HTTP/1.1
Host: t3a5h65dejiqek-8188.proxy.runpod.net
Content-Type: application/json

{
  "prompt": {
    "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "Qwen-Rapid-AIO-NSFW-v18.1.safetensors"}},
    "3": {"class_type": "TextEncodeQwenImageEditPlus", "inputs": {"clip": ["1", 1], "vae": ["1", 2], "prompt": "Full body portrait, athletic young woman, 23 years old, long blonde ponytail, blue eyes, wearing pink sports bra and black leggings, standing in park, golden hour, photorealistic, 8k, full body head to toe"}},
    "4": {"class_type": "TextEncodeQwenImageEditPlus", "inputs": {"clip": ["1", 1], "vae": ["1", 2], "prompt": "deformed, watermark, low quality, bad anatomy, blurry, ugly, cropped"}},
    "9": {"class_type": "EmptyLatentImage", "inputs": {"width": 768, "height": 1024, "batch_size": 1}},
    "2": {"class_type": "KSampler", "inputs": {"model": ["1", 0], "positive": ["3", 0], "negative": ["4", 0], "latent_image": ["9", 0], "seed": 42, "steps": 6, "cfg": 1.0, "sampler_name": "euler_ancestral", "scheduler": "beta", "denoise": 1.0}},
    "5": {"class_type": "VAEDecode", "inputs": {"samples": ["2", 0], "vae": ["1", 2]}},
    "6": {"class_type": "SaveImage", "inputs": {"images": ["5", 0], "filename_prefix": "api_t2i"}}
  }
}
```

**Respuesta:**
```json
{"prompt_id": "abc-123", "number": 1, "node_errors": {}}
```

### I2I - Subir imagen

```http
POST /upload/image HTTP/1.1
Host: t3a5h65dejiqek-8188.proxy.runpod.net
Content-Type: multipart/form-data; boundary=----Boundary

------Boundary
Content-Disposition: form-data; name="image"; filename="modelo.png"
Content-Type: image/png

(binary data)
------Boundary
Content-Disposition: form-data; name="type"

input
------Boundary
Content-Disposition: form-data; name="overwrite"

true
------Boundary--
```

**Respuesta:**
```json
{"name": "modelo.png", "subfolder": "", "type": "input"}
```

### I2I - Transformar con LoRA

```http
POST /api/prompt HTTP/1.1
Host: t3a5h65dejiqek-8188.proxy.runpod.net
Content-Type: application/json

{
  "prompt": {
    "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "Qwen-Rapid-AIO-NSFW-v18.1.safetensors"}},
    "10": {"class_type": "LoraLoader", "inputs": {"model": ["1", 0], "clip": ["1", 1], "lora_name": "Qwen-Image-Edit-F2P.safetensors", "strength_model": 0.7, "strength_clip": 0.7}},
    "7": {"class_type": "LoadImage", "inputs": {"image": "modelo.png", "upload": "image"}},
    "3": {"class_type": "TextEncodeQwenImageEditPlus", "inputs": {"clip": ["10", 1], "vae": ["1", 2], "prompt": "The same woman at tropical beach wearing white bikini, same face same eyes same skin, photorealistic, full body, 8k", "image1": ["7", 0]}},
    "4": {"class_type": "TextEncodeQwenImageEditPlus", "inputs": {"clip": ["10", 1], "vae": ["1", 2], "prompt": "different face, different person, deformed, bad anatomy, blurry, low quality, watermark"}},
    "9": {"class_type": "EmptyLatentImage", "inputs": {"width": 768, "height": 1024, "batch_size": 1}},
    "2": {"class_type": "KSampler", "inputs": {"model": ["10", 0], "positive": ["3", 0], "negative": ["4", 0], "latent_image": ["9", 0], "seed": 0, "steps": 8, "cfg": 1.0, "sampler_name": "euler_ancestral", "scheduler": "beta", "denoise": 0.65}},
    "5": {"class_type": "VAEDecode", "inputs": {"samples": ["2", 0], "vae": ["1", 2]}},
    "6": {"class_type": "SaveImage", "inputs": {"images": ["5", 0], "filename_prefix": "i2i_lora"}}
  }
}
```

### I2I - Transformar SIN LoRA

Mismo JSON pero sin nodo `"10"`, y `"3"`, `"4"`, `"2"` apuntan a `["1", ...]` en vez de `["10", ...]`.

### Obtener resultado

```http
GET /api/history/abc-123 HTTP/1.1
Host: t3a5h65dejiqek-8188.proxy.runpod.net
```

**Respuesta:**
```json
{
  "abc-123": {
    "status": {"status_str": "success", "completed": true},
    "outputs": {
      "6": {
        "images": [{"filename": "api_t2i_00001_.png", "subfolder": "", "type": "output"}]
      }
    }
  }
}
```

### Descargar imagen

```http
GET /view?filename=api_t2i_00001_.png&type=output HTTP/1.1
Host: t3a5h65dejiqek-8188.proxy.runpod.net
```

Retorna el binario PNG.

### Liberar VRAM

```http
POST /api/free HTTP/1.1
Host: t3a5h65dejiqek-8188.proxy.runpod.net
Content-Type: application/json

{"unload_models": true, "free_memory": true}
```

---

## Diferencia clave: Con LoRA vs Sin LoRA

La única diferencia en el JSON es:

**Sin LoRA:**
```
Checkpoint [1] ──> KSampler [2] (model)
Checkpoint [1] ──> TextEncode [3] (clip)
Checkpoint [1] ──> TextEncode [4] (clip)
```

**Con LoRA:**
```
Checkpoint [1] ──> LoraLoader [10] ──> KSampler [2] (model)
Checkpoint [1] ──> LoraLoader [10] ──> TextEncode [3] (clip)
Checkpoint [1] ──> LoraLoader [10] ──> TextEncode [4] (clip)
```

En el JSON cambia:
- Se agrega nodo `"10"` (LoraLoader)
- Nodos `"3"`, `"4"`: `"clip"` cambia de `["1", 1]` a `["10", 1]`
- Nodo `"2"`: `"model"` cambia de `["1", 0]` a `["10", 0]`

---

## Parámetros de Referencia

### Denoise (solo I2I)
| Valor | Efecto |
|-------|--------|
| 0.35 - 0.45 | Cambio mínimo (color de pelo) |
| 0.45 - 0.55 | Cambio de ropa |
| 0.55 - 0.65 | Ropa + pelo |
| 0.65 - 0.75 | Ropa + pelo + escena |
| 0.75 - 0.85 | Transformación completa |

### Steps
| Valor | Uso |
|-------|-----|
| 4 | Rápido, calidad aceptable |
| 6 | Balance calidad/velocidad (recomendado) |
| 8 | Alta calidad para cambios complejos |

### Resolución
| Tamaño | Uso |
|--------|-----|
| 768 x 1024 | Vertical, cuerpo entero (recomendado) |
| 1024 x 768 | Horizontal, paisaje |
| 768 x 768 | Cuadrado |

### Seed
| Valor | Comportamiento |
|-------|---------------|
| 0 | Random (ComfyUI elige) |
| 1-999999999 | Fijo, reproduce el mismo resultado |

---

## Tiempos de Respuesta (RTX 5090)

| Operación | Primera vez | Siguientes |
|-----------|------------|------------|
| T2I (6 steps) | ~75s | ~4-5s |
| I2I (8 steps) | ~75s | ~5-6s |
| Upload imagen | - | <1s |
| Download imagen | - | <1s |
| Free memory | - | <1s |

La primera ejecución carga el modelo en VRAM (27GB). Las siguientes usan el modelo cacheado.

---

## Manejo de Errores

### Prompt inválido
```json
{
  "error": {
    "type": "prompt_outputs_failed_validation",
    "message": "Prompt outputs failed validation"
  },
  "node_errors": {
    "7": {
      "errors": [{"type": "custom_validation_failed", "message": "Invalid image file: foto.png"}]
    }
  }
}
```

### Resultado no listo
Si `GET /api/history/{id}` retorna `{}` (vacío), el prompt aún está procesándose. Reintentar en 2 segundos.

### Cola llena
Verificar con `GET /api/queue`. Si hay muchos pending, esperar antes de enviar más.

---

## Monitoreo

### Health Check
```bash
curl https://t3a5h65dejiqek-8188.proxy.runpod.net/api/system_stats
```

### VRAM
Desde el response de system_stats:
```json
{
  "devices": [{"vram_total": 32607, "vram_free": 4000}]
}
```

### Watcher
El proceso watcher en el pod:
- Reinicia ComfyUI automáticamente si se cae
- Limpia VRAM si supera 90%
- Limpia archivos de output >24h
- Health check cada 30 segundos

---

## Archivos en el Repositorio

```
i2i/
├── docs/
│   ├── reference.md              # Info rápida del pod
│   ├── setup-log.md              # Log de instalación
│   ├── api-guide.md              # Guía de API con ejemplos
│   └── integration-guide.md      # Esta guía
├── src/
│   ├── api/
│   │   ├── endpoints.json        # Documentación de endpoints
│   │   ├── workflow_templates.json    # Templates parametrizados
│   │   ├── i2i_with_lora_template.json # Template I2I con LoRA switchable
│   │   └── templates_catalog.json     # Catálogo unificado (tu formato)
│   ├── services/
│   │   ├── comfyui_watcher.py    # Watcher auto-restart + GC
│   │   └── startup.sh            # Script de inicio del pod
│   └── prompts/
│       └── catalog.json          # Catálogo sportswear original
├── workflows/
│   ├── t2i/
│   │   ├── workflow_t2i.json     # Workflow T2I (formato API)
│   │   ├── catalog.json          # Sportswear (6 modelos)
│   │   ├── catalog_swimwear.json # Swimwear (8 modelos)
│   │   ├── catalog_casual_summer.json  # Casual (12 modelos)
│   │   ├── catalog_intimates.json      # Intimates (12 modelos)
│   │   ├── catalog_young_fashion.json  # Young Fashion (12 modelos)
│   │   ├── catalog_accessories.json    # Accessories (8 modelos)
│   │   ├── catalog_executive_gym.json  # Gym (12 modelos)
│   │   └── README.md
│   ├── i2i/
│   │   ├── workflow_*.json       # 5 workflows I2I (formato API)
│   │   ├── supercatalog_scenes.json  # 20 escenas predefinidas
│   │   └── README.md
│   ├── i2v/
│   │   ├── workflow_i2v.json     # Workflow video (pendiente)
│   │   ├── video_scripts.json    # 10 guiones de video
│   │   └── README.md
│   └── original/
│       └── Qwen-Rapid-AIO.json  # Workflow original Phr00t
```
