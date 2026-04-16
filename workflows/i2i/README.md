# Image-to-Image (I2I) Workflows

Workflows para transformar imágenes existentes usando Qwen Image Edit. Reciben una imagen de entrada y generan una versión modificada preservando la identidad de la persona.

## Workflows disponibles

### 1. `workflow_change_outfit.json` — Cambio de Ropa
Cambia la ropa de la modelo manteniendo cara, cuerpo, pose y escena.

| Parámetro | Valor | Notas |
|-----------|-------|-------|
| Denoise | **0.55** | Moderado: cambia ropa sin alterar identidad |
| Steps | 6 | |
| CFG | 1.0 | |

**Prompt positivo ejemplo:**
```
The same woman wearing a red summer dress with white polka dots, same face, same body, same pose, same background, photorealistic
```

### 2. `workflow_change_hair.json` — Cambio de Pelo
Cambia color, largo o estilo de pelo manteniendo todo lo demás.

| Parámetro | Valor | Notas |
|-----------|-------|-------|
| Denoise | **0.45** | Bajo: cambio sutil, solo pelo |
| Steps | 6 | |
| CFG | 1.0 | |

**Prompt positivo ejemplo:**
```
The same woman with short platinum blonde pixie cut hair, same face, same outfit, same pose, same background, photorealistic
```

### 3. `workflow_full_transform.json` — Transformación Completa
Cambia ropa, pelo y opcionalmente escena. Cambio profundo pero preserva rasgos faciales.

| Parámetro | Valor | Notas |
|-----------|-------|-------|
| Denoise | **0.65** | Alto: permite cambios profundos |
| Steps | 8 | Más steps para mayor coherencia |
| CFG | 1.0 | |

**Prompt positivo ejemplo:**
```
The same woman with short black bob hair, wearing a blue business suit and heels, standing in modern office lobby, same face, same skin, photorealistic
```

## Guía de denoise para I2I
- **0.35 - 0.45:** Cambios mínimos (solo color de pelo, ajuste de tono)
- **0.45 - 0.55:** Cambios moderados (cambio de ropa, accesorios)
- **0.55 - 0.65:** Cambios significativos (ropa + pelo)
- **0.65 - 0.75:** Cambios profundos (ropa + pelo + escena)

## Tips para mejores resultados
- Siempre incluir "same face, same body, same skin" en el prompt positivo
- El prompt negativo ya incluye protección de identidad
- Para cambios de ropa: describir la nueva ropa en detalle, no mencionar la ropa vieja
- Para cambios de pelo: describir el nuevo pelo, agregar "same outfit" al positivo
- Si la identidad se pierde: bajar denoise 0.05
- Si el cambio no es suficiente: subir denoise 0.05

### 4. `workflow_restyle.json` — Restyle Completo (Cuerpo + Escena + Ropa)
Transforma una modelo completamente: ajusta tipo de cuerpo (más flaca/gordita), cambia escenario y ropa. Preserva rasgos faciales.

| Parámetro | Valor | Notas |
|-----------|-------|-------|
| Denoise | **0.70** | Alto: permite cambios de cuerpo y escena |
| Steps | 8 | Más steps para coherencia en cambios grandes |
| CFG | 1.0 | |

**Ejemplos de prompt:**

Chica urbana → chica en la playa:
```
The same woman but slightly slimmer, at a tropical beach, wearing a white bikini top and denim cutoff shorts, barefoot on sand, ocean waves in background, same face, same eyes, same skin tone, photorealistic, full body head to toe
```

Hacer más curvy:
```
The same woman but with a curvier fuller body, wider hips, same face, same outfit, same pose, same background, photorealistic, natural body proportions
```

Hacer más slim:
```
The same woman but slimmer and more toned, athletic build, same face, same outfit, same pose, same background, photorealistic, natural body proportions
```

## Uso via API

### 1. Subir imagen
```bash
curl -X POST http://localhost:8188/upload/image \
  -F "image=@modelo_original.png" \
  -F "type=input"
```

### 2. Ejecutar
Reemplazar `INPUT_IMAGE` con el nombre del archivo subido y el prompt placeholder:
```bash
curl -X POST http://localhost:8188/api/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": <workflow_json>}'
```
