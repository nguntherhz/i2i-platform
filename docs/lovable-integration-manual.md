# Manual de Integración: Engine Lovable + i2i ComfyUI API

## Objetivo

Integrar el engine de contenido de Lovable con la API de ComfyUI para generar y transformar imágenes de personas ficticias bajo demanda. El engine envía templates con prompts y recibe imágenes generadas.

---

## Arquitectura

```
┌─────────────┐      HTTPS/JSON       ┌──────────────────────┐
│             │  ──────────────────>   │                      │
│   Lovable   │                        │  ComfyUI API         │
│   Engine    │  <──────────────────   │  (RunPod GPU Pod)    │
│             │      PNG/MP4           │                      │
└─────────────┘                        └──────────────────────┘
                                              │
                                       ┌──────┴──────┐
                                       │ RTX 5090    │
                                       │ 32GB VRAM   │
                                       │ Qwen Model  │
                                       │ + LoRAs     │
                                       └─────────────┘
```

---

## Conexión

```
BASE_URL = https://t3a5h65dejiqek-8188.proxy.runpod.net
```

- Sin autenticación (URL obscura como seguridad)
- CORS habilitado
- Timeout recomendado: 120s (primera ejecución carga modelo)

---

## Estructura del Template (formato Lovable)

El engine ya maneja templates con esta estructura:

```json
{
  "id": "unique-id",
  "metadata": {
    "title": "Nombre del template",
    "description": "Descripción",
    "category": "Categoría"
  },
  "category": "Categoría",
  "workflow_type": "t2i | i2i",
  "lora": null,
  "workflow_params": {
    "prompts": {
      "positive": "prompt positivo...",
      "negative": "prompt negativo..."
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

**Campos nuevos respecto al template existente de video:**
- `workflow_type`: `"t2i"` (texto a imagen) o `"i2i"` (imagen a imagen)
- `lora`: `null` o `{"name": "archivo.safetensors", "strength_model": 0.7, "strength_clip": 0.7}`
- `image_config`: reemplaza `video_config` para flujos de imagen

---

## Implementación en el Engine

### Paso 1: Función para construir el payload de ComfyUI

El engine debe convertir un template Lovable en el JSON que ComfyUI espera.

```javascript
function buildComfyUIPayload(template, options = {}) {
  const { inputImage = null, seed = 0 } = options;
  const { prompts, image_config } = template.workflow_params;
  const lora = template.lora;
  const actualSeed = seed > 0 ? seed : Math.floor(Math.random() * 999999999);

  const workflow = {};

  // Nodo 1: Cargar modelo base
  workflow["1"] = {
    class_type: "CheckpointLoaderSimple",
    inputs: { ckpt_name: "Qwen-Rapid-AIO-NSFW-v18.1.safetensors" }
  };

  // Determinar fuente de model/clip (directo o via LoRA)
  let modelSource = "1";
  let clipSource = "1";

  // Nodo 10: LoRA (opcional)
  if (lora && lora.name) {
    workflow["10"] = {
      class_type: "LoraLoader",
      inputs: {
        model: ["1", 0],
        clip: ["1", 1],
        lora_name: lora.name,
        strength_model: lora.strength_model,
        strength_clip: lora.strength_clip
      }
    };
    modelSource = "10";
    clipSource = "10";
  }

  // Nodo 7: Imagen de entrada (solo I2I)
  if (template.workflow_type === "i2i" && inputImage) {
    workflow["7"] = {
      class_type: "LoadImage",
      inputs: { image: inputImage, upload: "image" }
    };
  }

  // Nodo 3: Prompt positivo
  const positiveNode = {
    class_type: "TextEncodeQwenImageEditPlus",
    inputs: {
      clip: [clipSource, 1],
      vae: ["1", 2],
      prompt: prompts.positive
    }
  };
  if (template.workflow_type === "i2i" && inputImage) {
    positiveNode.inputs.image1 = ["7", 0];
  }
  workflow["3"] = positiveNode;

  // Nodo 4: Prompt negativo
  workflow["4"] = {
    class_type: "TextEncodeQwenImageEditPlus",
    inputs: {
      clip: [clipSource, 1],
      vae: ["1", 2],
      prompt: prompts.negative
    }
  };

  // Nodo 9: Tamaño de salida
  workflow["9"] = {
    class_type: "EmptyLatentImage",
    inputs: {
      width: image_config.width,
      height: image_config.height,
      batch_size: 1
    }
  };

  // Nodo 2: Sampler
  workflow["2"] = {
    class_type: "KSampler",
    inputs: {
      model: [modelSource, 0],
      positive: ["3", 0],
      negative: ["4", 0],
      latent_image: ["9", 0],
      seed: actualSeed,
      steps: image_config.steps,
      cfg: image_config.cfg,
      sampler_name: image_config.sampler,
      scheduler: image_config.scheduler,
      denoise: image_config.denoise
    }
  };

  // Nodo 5: Decodificar
  workflow["5"] = {
    class_type: "VAEDecode",
    inputs: { samples: ["2", 0], vae: ["1", 2] }
  };

  // Nodo 6: Guardar
  workflow["6"] = {
    class_type: "SaveImage",
    inputs: {
      images: ["5", 0],
      filename_prefix: template.id
    }
  };

  return { prompt: workflow };
}
```

### Paso 2: Función para subir imagen (solo I2I)

```javascript
async function uploadImage(file) {
  const formData = new FormData();
  formData.append("image", file);
  formData.append("type", "input");
  formData.append("overwrite", "true");

  const response = await fetch(`${BASE_URL}/upload/image`, {
    method: "POST",
    body: formData
  });

  const data = await response.json();
  return data.name; // nombre del archivo en el servidor
}
```

### Paso 3: Función para ejecutar y obtener resultado

```javascript
async function generateImage(template, options = {}) {
  const { inputImage = null, seed = 0, pollInterval = 2000, timeout = 120000 } = options;

  // 1. Si es I2I, subir imagen primero
  let uploadedImageName = null;
  if (template.workflow_type === "i2i" && inputImage) {
    uploadedImageName = await uploadImage(inputImage);
  }

  // 2. Construir y enviar payload
  const payload = buildComfyUIPayload(template, {
    inputImage: uploadedImageName,
    seed
  });

  const queueResponse = await fetch(`${BASE_URL}/api/prompt`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  const queueData = await queueResponse.json();

  if (queueData.node_errors && Object.keys(queueData.node_errors).length > 0) {
    throw new Error(`ComfyUI validation error: ${JSON.stringify(queueData.node_errors)}`);
  }

  const promptId = queueData.prompt_id;

  // 3. Polling hasta obtener resultado
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    const historyResponse = await fetch(`${BASE_URL}/api/history/${promptId}`);
    const historyData = await historyResponse.json();

    if (historyData[promptId]) {
      const status = historyData[promptId].status?.status_str;

      if (status === "success") {
        const outputs = historyData[promptId].outputs;
        const images = outputs["6"]?.images;

        if (images && images.length > 0) {
          const filename = images[0].filename;
          const imageUrl = `${BASE_URL}/view?filename=${encodeURIComponent(filename)}&type=output`;

          return {
            success: true,
            promptId,
            filename,
            imageUrl,
            downloadUrl: imageUrl
          };
        }
      }

      if (status === "error") {
        throw new Error(`Generation failed for prompt ${promptId}`);
      }
    }

    await new Promise(resolve => setTimeout(resolve, pollInterval));
  }

  throw new Error(`Timeout waiting for prompt ${promptId}`);
}
```

### Paso 4: Función para descargar la imagen como blob

```javascript
async function downloadImage(imageUrl) {
  const response = await fetch(imageUrl);
  const blob = await response.blob();
  return blob;
}
```

---

## Uso desde Lovable

### Generar persona ficticia (T2I)

```javascript
const template = {
  id: "t2i-sportswear-001",
  metadata: { title: "Sportswear Model", description: "...", category: "Sportswear" },
  category: "Sportswear",
  workflow_type: "t2i",
  lora: null,
  workflow_params: {
    prompts: {
      positive: "Full body portrait, athletic young woman, 23 years old...",
      negative: "deformed, watermark, low quality..."
    },
    image_config: {
      width: 768, height: 1024, steps: 6,
      cfg: 1.0, denoise: 1.0,
      sampler: "euler_ancestral", scheduler: "beta"
    }
  }
};

const result = await generateImage(template);
console.log(result.imageUrl); // URL para descargar la imagen
```

### Transformar imagen existente (I2I)

```javascript
const template = {
  id: "i2i-restyle-001",
  workflow_type: "i2i",
  lora: null,
  workflow_params: {
    prompts: {
      positive: "The same woman at tropical beach wearing white bikini, same face same eyes, photorealistic, full body, 8k",
      negative: "different face, different person, deformed, blurry, low quality"
    },
    image_config: {
      width: 768, height: 1024, steps: 8,
      cfg: 1.0, denoise: 0.72,
      sampler: "euler_ancestral", scheduler: "beta"
    }
  }
};

// inputImage es un File object del input del usuario
const result = await generateImage(template, { inputImage: userFile });
console.log(result.imageUrl);
```

### Transformar con LoRA (preservar cara)

```javascript
const template = {
  id: "i2i-lora-face-001",
  workflow_type: "i2i",
  lora: {
    name: "Qwen-Image-Edit-F2P.safetensors",
    strength_model: 0.7,
    strength_clip: 0.7
  },
  workflow_params: {
    prompts: {
      positive: "The same woman in office wearing blue business suit, same face same skin, photorealistic, full body",
      negative: "different face, different person, deformed, blurry"
    },
    image_config: {
      width: 768, height: 1024, steps: 8,
      cfg: 1.0, denoise: 0.65,
      sampler: "euler_ancestral", scheduler: "beta"
    }
  }
};

const result = await generateImage(template, { inputImage: userFile });
```

---

## Categorías y LoRAs Disponibles

| Categoría | workflow_type | LoRA | denoise |
|-----------|-------------|------|---------|
| Sportswear | t2i | null | 1.0 |
| Swimwear | t2i | null | 1.0 |
| Casual Summer | t2i | null | 1.0 |
| Intimates | t2i | null | 1.0 |
| Young Fashion | t2i | null | 1.0 |
| Accessories | t2i | null | 1.0 |
| Executive Gym | t2i | null | 1.0 |
| I2I Change Hair | i2i | null | 0.45 |
| I2I Change Outfit | i2i | null | 0.55 |
| I2I Restyle | i2i | null | 0.75 |
| I2I Super Catalog | i2i | null | 0.72 |
| I2I with Face LoRA | i2i | F2P (0.7) | 0.65 |

---

## Health Check y Monitoreo

### Verificar si la API está disponible

```javascript
async function isAPIHealthy() {
  try {
    const response = await fetch(`${BASE_URL}/api/system_stats`, { 
      signal: AbortSignal.timeout(5000) 
    });
    const data = await response.json();
    return data.system?.comfyui_version ? true : false;
  } catch {
    return false;
  }
}
```

### Verificar cola

```javascript
async function getQueueStatus() {
  const response = await fetch(`${BASE_URL}/api/queue`);
  const data = await response.json();
  return {
    running: data.queue_running?.length || 0,
    pending: data.queue_pending?.length || 0
  };
}
```

### Liberar VRAM (después de muchas generaciones)

```javascript
async function freeMemory() {
  await fetch(`${BASE_URL}/api/free`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ unload_models: true, free_memory: true })
  });
}
```

---

## Tiempos Esperados

| Operación | Primera vez | Cache caliente |
|-----------|------------|---------------|
| T2I (6 steps) | ~75s | ~4-5s |
| I2I (6 steps) | ~75s | ~5s |
| I2I (8 steps) | ~75s | ~6s |
| Upload imagen | - | <1s |
| Download imagen | - | <1s |

**Nota:** La primera ejecución después de reiniciar el pod o liberar VRAM tarda ~75s porque carga el modelo (27GB) en la GPU. Todas las siguientes son rápidas.

---

## Flujo I2V (Image-to-Video)

El engine también soporta generación de video a partir de una imagen estática. Esto corre en un **pod separado** dedicado a video.

### Template I2V

```json
{
  "id": "i2v-walking-001",
  "metadata": {
    "title": "Walking Confidence",
    "description": "Woman starts walking forward with hair bouncing",
    "category": "I2V Lifestyle"
  },
  "category": "I2V Lifestyle",
  "workflow_type": "i2v",
  "lora": null,
  "workflow_params": {
    "prompts": {
      "positive": "The woman starts walking forward confidently, hair bouncing with each step, slight smile, smooth natural motion",
      "negative": ""
    },
    "video_config": {
      "width": 640,
      "height": 640,
      "num_frames": 81,
      "fps": 24,
      "steps": 4,
      "cfg": 1.0,
      "denoise": 1.0,
      "sampler": "sa_solver",
      "scheduler": "beta"
    }
  }
}
```

### Diferencias con T2I/I2I

| Aspecto | T2I / I2I | I2V |
|---------|-----------|-----|
| `workflow_type` | `"t2i"` / `"i2i"` | `"i2v"` |
| Config | `image_config` | `video_config` |
| Output | `.png` | `.mp4` |
| Pod | Pod de imágenes | Pod de video (separado) |
| Base URL | `BASE_URL_IMAGE` | `BASE_URL_VIDEO` |
| Modelo | Qwen NSFW v18.1 | Wan 2.2 I2V |
| Tiempo | ~5s | ~30-40s |

### buildComfyUIPayload para I2V

```javascript
function buildComfyUIPayloadI2V(template, options = {}) {
  const { inputImage, seed = 0 } = options;
  const { prompts, video_config } = template.workflow_params;
  const actualSeed = seed > 0 ? seed : Math.floor(Math.random() * 999999999);

  return {
    prompt: {
      "1": {
        class_type: "CheckpointLoaderSimple",
        inputs: { ckpt_name: "wan2.2-i2v-rapid-aio.safetensors" }
      },
      "12": {
        class_type: "CLIPVisionLoader",
        inputs: { clip_name: "clip-vision_vit-h.safetensors" }
      },
      "10": {
        class_type: "LoadImage",
        inputs: { image: inputImage, upload: "image" }
      },
      "5": {
        class_type: "CLIPTextEncode",
        inputs: { clip: ["1", 1], text: prompts.positive }
      },
      "4": {
        class_type: "CLIPTextEncode",
        inputs: { clip: ["1", 1], text: prompts.negative || "" }
      },
      "11": {
        class_type: "CLIPVisionEncode",
        inputs: { clip_vision: ["12", 0], image: ["10", 0], crop: "center" }
      },
      "9": {
        class_type: "WanImageToVideo",
        inputs: {
          positive: ["5", 0],
          negative: ["4", 0],
          vae: ["1", 2],
          clip_vision_output: ["11", 0],
          start_image: ["10", 0],
          width: video_config.width,
          height: video_config.height,
          length: video_config.num_frames,
          batch_size: 1
        }
      },
      "2": {
        class_type: "ModelSamplingSD3",
        inputs: { model: ["1", 0], shift: 8.0 }
      },
      "3": {
        class_type: "KSampler",
        inputs: {
          model: ["2", 0],
          positive: ["9", 0],
          negative: ["9", 1],
          latent_image: ["9", 2],
          seed: actualSeed,
          steps: video_config.steps,
          cfg: video_config.cfg,
          sampler_name: video_config.sampler,
          scheduler: video_config.scheduler,
          denoise: video_config.denoise
        }
      },
      "7": {
        class_type: "VAEDecode",
        inputs: { samples: ["3", 0], vae: ["1", 2] }
      },
      "8": {
        class_type: "VHS_VideoCombine",
        inputs: {
          images: ["7", 0],
          frame_rate: video_config.fps,
          loop_count: 0,
          filename_prefix: template.id,
          format: "video/h264-mp4",
          pix_fmt: "yuv420p",
          crf: 19,
          save_metadata: true,
          trim_to_audio: false,
          pingpong: false,
          save_output: true
        }
      }
    }
  };
}
```

### Función unificada de generación

```javascript
async function generate(template, options = {}) {
  // Seleccionar base URL según tipo de workflow
  const baseUrl = template.workflow_type === "i2v" ? BASE_URL_VIDEO : BASE_URL_IMAGE;

  // Subir imagen si es I2I o I2V
  let uploadedImageName = null;
  if ((template.workflow_type === "i2i" || template.workflow_type === "i2v") && options.inputImage) {
    uploadedImageName = await uploadImage(options.inputImage, baseUrl);
  }

  // Construir payload según tipo
  let payload;
  switch (template.workflow_type) {
    case "t2i":
    case "i2i":
      payload = buildComfyUIPayload(template, { inputImage: uploadedImageName, seed: options.seed });
      break;
    case "i2v":
      payload = buildComfyUIPayloadI2V(template, { inputImage: uploadedImageName, seed: options.seed });
      break;
    default:
      throw new Error(`Unknown workflow_type: ${template.workflow_type}`);
  }

  // Ejecutar
  const queueResponse = await fetch(`${baseUrl}/api/prompt`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  const queueData = await queueResponse.json();
  if (queueData.node_errors && Object.keys(queueData.node_errors).length > 0) {
    throw new Error(`ComfyUI error: ${JSON.stringify(queueData.node_errors)}`);
  }

  const promptId = queueData.prompt_id;

  // Polling (timeout más largo para video)
  const timeout = template.workflow_type === "i2v" ? 300000 : 120000;
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    const historyResponse = await fetch(`${baseUrl}/api/history/${promptId}`);
    const historyData = await historyResponse.json();

    if (historyData[promptId]?.status?.status_str === "success") {
      const outputs = historyData[promptId].outputs;

      // Video output está en nodo "8", imagen en nodo "6"
      const outputNode = template.workflow_type === "i2v" ? "8" : "6";
      const outputKey = template.workflow_type === "i2v" ? "gifs" : "images";
      const files = outputs[outputNode]?.[outputKey] || outputs[outputNode]?.images || [];

      if (files.length > 0) {
        const filename = files[0].filename;
        return {
          success: true,
          promptId,
          filename,
          type: template.workflow_type === "i2v" ? "video" : "image",
          downloadUrl: `${baseUrl}/view?filename=${encodeURIComponent(filename)}&type=output`
        };
      }
    }

    if (historyData[promptId]?.status?.status_str === "error") {
      throw new Error(`Generation failed: ${promptId}`);
    }

    await new Promise(r => setTimeout(r, 2000));
  }

  throw new Error(`Timeout: ${promptId}`);
}
```

### Categorías I2V disponibles

| ID | Categoría | Descripción |
|----|-----------|-------------|
| i2v-walking-001 | Lifestyle | Caminar con confianza |
| i2v-office-home-001 | Lifestyle transition | Oficina a casa, sacarse blazer |
| i2v-beach-city-001 | Scene transition | Playa a ciudad |
| i2v-sport-sleep-001 | Outfit transition | Ropa deportiva a pijama |
| i2v-stand-sit-001 | Pose transition | Parada a sentada |
| i2v-sit-lie-001 | Pose transition | Sentada a acostada |
| i2v-yoga-001 | Dynamic action | Secuencia de yoga |
| i2v-hair-flip-001 | Beauty moment | Flip de pelo + sonrisa |
| i2v-pool-001 | Scene action | Entrar a la piscina |
| i2v-coffee-001 | Lifestyle moment | Tomar café en la mañana |

### Configuración de URLs

```javascript
const BASE_URL_IMAGE = "https://t3a5h65dejiqek-8188.proxy.runpod.net";  // Pod imágenes
const BASE_URL_VIDEO = "https://PENDIENTE-VIDEO-POD.proxy.runpod.net";   // Pod video (por configurar)
```

---

## Manejo de Errores

| Error | Causa | Acción |
|-------|-------|--------|
| HTTP 400 + `node_errors` | Prompt inválido, imagen no encontrada | Verificar JSON y nombre de imagen |
| HTTP 500 | ComfyUI crash | El watcher lo reinicia. Reintentar en 30s |
| Timeout en polling | Modelo cargándose por primera vez | Aumentar timeout a 120s |
| `{}` en history | Aún procesándose | Seguir polling |
| CORS error | URL base incorrecta | Verificar BASE_URL |
| Connection refused | Pod apagado o reiniciándose | Verificar pod en RunPod dashboard |

### Retry recomendado

```javascript
async function generateWithRetry(template, options = {}, maxRetries = 2) {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await generateImage(template, options);
    } catch (error) {
      if (attempt === maxRetries) throw error;
      
      // Si es timeout, puede ser carga de modelo. Reintentar
      console.warn(`Attempt ${attempt + 1} failed: ${error.message}. Retrying...`);
      await new Promise(r => setTimeout(r, 5000));
    }
  }
}
```

---

## Checklist de Integración

- [ ] Configurar `BASE_URL` en variables de entorno
- [ ] Implementar `buildComfyUIPayload()` 
- [ ] Implementar `uploadImage()` para I2I
- [ ] Implementar `generateImage()` con polling
- [ ] Implementar `isAPIHealthy()` para health check
- [ ] Agregar templates al catálogo del engine
- [ ] Configurar timeout de 120s para primera ejecución
- [ ] Agregar retry logic (2 reintentos)
- [ ] Testear flujo T2I completo
- [ ] Testear flujo I2I completo (upload + transform)
- [ ] Testear flujo I2I con LoRA
- [ ] Verificar que las imágenes se rendericen correctamente en el frontend
