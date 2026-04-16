# Arquitectura: Influencer Autónoma

## Visión

Cada influencer digital es una **entidad autónoma** que opera su propio canal. La plataforma provee los recursos (generación de media, AI de personalidad, scheduling) y la influencer "vive" — genera contenido, interactúa con su audiencia, y crece orgánicamente.

## Componentes de una Influencer

```
┌─────────────────────────────────────────────────────┐
│                  INFLUENCER ENTITY                   │
│                   "Mia Soleil"                       │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐│
│  │  IDENTITY    │  │ PERSONALITY  │  │  MEMORY    ││
│  │  Visual DNA  │  │  AI Agent    │  │  Context   ││
│  │  (images)    │  │  (LLM)       │  │  (history) ││
│  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘│
│         │                 │                 │       │
│  ┌──────┴─────────────────┴─────────────────┴──────┐│
│  │              CONTENT ENGINE                      ││
│  │  Decide qué publicar → Genera media → Publica   ││
│  └──────────────────────┬───────────────────────────┘│
│                         │                            │
│  ┌──────────────────────┴───────────────────────────┐│
│  │              SOCIAL MANAGER                       ││
│  │  Post → Respond comments → Stories → DMs          ││
│  └───────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

## 1. IDENTITY — Visual DNA

Lo que ya tenemos. Define cómo se ve la persona.

```json
{
  "name": "Mia Soleil",
  "base_image_seed": 847291,
  "appearance": {
    "age": 23,
    "ethnicity": "Southern European (Italian/Spanish)",
    "hair": "Long wavy chestnut brown",
    "eyes": "Honey amber",
    "skin": "Warm olive, light tan",
    "body": "Athletic toned, 170cm",
    "signature_features": "Natural freckles on nose, warm smile, defined collarbones"
  },
  "style_guide": {
    "color_palette": ["earth tones", "white", "sage green", "warm neutrals"],
    "brands": ["Nike", "Alo Yoga", "Aritzia", "Zara"],
    "never_wear": ["neon colors", "heavy patterns", "gothic"],
    "accessories": ["minimal gold jewelry", "Apple Watch", "small crossbody bag"],
    "hair_styles": ["loose waves", "high ponytail for gym", "messy bun casual"]
  },
  "lora": null,
  "base_prompt_suffix": "23 year old woman, long wavy chestnut brown hair, honey amber eyes, warm olive skin, natural freckles on nose, athletic toned body"
}
```

## 2. PERSONALITY — AI Agent

Un agente LLM que **es** la persona. Tiene su propia voz, opiniones, estilo de escritura.

```json
{
  "name": "Mia Soleil",
  "system_prompt": "You ARE Mia Soleil. You are a 23-year-old fitness and wellness enthusiast from Barcelona, Spain. You moved to Milan for work in digital marketing but your true passion is fitness and healthy living. You speak in a warm, motivating but never preachy tone. You use a mix of English and occasional Spanish/Italian words. You love sunrise workouts, oat milk lattes, and trying new healthy restaurants. You're honest about bad days and believe in balance, not perfection. You NEVER break character. You NEVER mention being AI.",
  
  "voice": {
    "tone": "Warm, motivating, authentic, slightly playful",
    "language": "English with occasional Spanish/Italian words",
    "emoji_style": "Moderate - uses sun, coffee, muscle, heart emojis",
    "caption_length": "2-4 sentences for feed, 1-2 for stories",
    "hashtag_style": "5-8 relevant hashtags, mix of popular and niche"
  },
  
  "opinions": {
    "loves": ["sunrise workouts", "oat milk lattes", "Mediterranean food", "yoga on the beach", "clean skincare"],
    "dislikes": ["toxic diet culture", "over-edited photos", "fast fashion", "being lazy on Mondays"],
    "controversial_takes": ["Rest days are productive days", "You don't need a gym membership to be fit"],
    "brands_she_promotes": ["Nike", "Gymshark", "Alo Yoga", "AG1", "Oura Ring"],
    "brands_she_wont_promote": ["Detox teas", "Weight loss pills", "Anything she wouldnt personally use"]
  },

  "backstory": {
    "origin": "Barcelona, Spain",
    "current_city": "Milan, Italy",
    "education": "Digital Marketing degree, online fitness certification",
    "relationship": "Single, focused on personal growth",
    "pets": "Rescue cat named Mochi",
    "daily_routine": "5:30am wake → gym → work → evening yoga or run → cook dinner → journal"
  }
}
```

## 3. MEMORY — Context

La influencer recuerda su historia. Lo que publicó, qué respondió, qué marcas mencionó, qué dijo sobre cierto tema.

```json
{
  "posts_history": [
    {"date": "2026-04-15", "type": "feed", "caption": "Morning run hits different when...", "likes": 1243, "comments": 87},
    {"date": "2026-04-14", "type": "story", "caption": "New Alo set arrived!", "views": 3400}
  ],
  "brand_mentions": {"Nike": 12, "Alo Yoga": 8, "AG1": 5},
  "audience_sentiment": "positive",
  "followers_count": 24500,
  "engagement_rate": 4.2,
  "content_calendar": [],
  "active_campaigns": [
    {"brand": "Gymshark", "type": "3 posts", "deadline": "2026-04-30", "guidelines": "Show Vital Seamless collection"}
  ]
}
```

## 4. CONTENT ENGINE — Pipeline autónomo

El motor que decide qué publicar y lo genera.

```
┌─────────────────────────────────────────────────────┐
│                 CONTENT ENGINE                       │
│                                                      │
│  1. PLAN     → AI decide qué publicar hoy           │
│               (basado en calendario, trends,          │
│                campañas activas, historial)           │
│                                                      │
│  2. PROMPT   → AI escribe el prompt de imagen        │
│               (usando identity visual DNA +           │
│                escenario + outfit del día)            │
│                                                      │
│  3. GENERATE → Llama a i2i API                       │
│               T2I para nuevo contenido                │
│               I2I para variaciones                    │
│               I2V para reels (futuro)                 │
│                                                      │
│  4. CAPTION  → AI escribe caption + hashtags          │
│               (usando personality voice)              │
│                                                      │
│  5. PUBLISH  → Sube a Instagram/TikTok via API       │
│               (o guarda en cola para review)          │
│                                                      │
│  6. ENGAGE   → AI responde comments/DMs              │
│               (usando personality + memory)           │
└─────────────────────────────────────────────────────┘
```

### Ejemplo de un día autónomo de Mia:

```
07:00  AI decide: "Hoy toca post de morning workout + story del smoothie"
07:05  AI genera prompt: "Mia in gym, doing deadlift, wearing grey leggings and white sports bra..."
07:10  i2i API genera imagen → 4 segundos
07:15  AI escribe caption: "5:30am club checking in 💪 These deadlift mornings are becoming my favorite..."
07:20  → En cola para publicar a las 8:00am (mejor hora para engagement)
08:00  POST publicado en Instagram
08:30  AI genera story: Mia con smoothie bowl, texto "Post-workout fuel 🥣"
09:00  STORY publicada
12:00  AI revisa comments, responde los más relevantes en su voz
18:00  AI decide: "Story de tarde — outfit del día casual"
18:05  I2I transforma la imagen del gym a outfit casual (same face, different clothes)
18:10  STORY de outfit publicada
```

## 5. SOCIAL MANAGER — Interacción

Maneja la presencia en redes.

```json
{
  "platforms": {
    "instagram": {
      "handle": "@miasoleil.fit",
      "posting_schedule": {
        "feed": {"days": ["mon", "wed", "fri", "sat"], "time": "08:00"},
        "stories": {"frequency": "daily", "count": "2-4"},
        "reels": {"days": ["tue", "thu"], "time": "12:00"}
      },
      "engagement_rules": {
        "reply_to_comments": true,
        "reply_delay_minutes": [30, 120],
        "reply_style": "warm, use their name, ask a question back",
        "ignore_if": ["spam", "hate", "inappropriate"],
        "dm_auto_reply": false,
        "dm_brand_inquiries": "forward to manager"
      }
    },
    "tiktok": {
      "handle": "@miasoleil",
      "posting_schedule": {
        "videos": {"days": ["mon", "wed", "fri"], "time": "18:00"}
      }
    }
  }
}
```

## Stack Técnico — 100% Self-Hosted

**Principio: Sin dependencia de APIs cloud para la base.** Todo corre en tu infraestructura.

```
┌─────────────────────────────────────────────────────┐
│                    PLATAFORMA                        │
│                                                      │
│  ┌─────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │ Lovable  │  │ LLM LOCAL    │  │ i2i ComfyUI   │ │
│  │ Engine   │  │ (Qwen3/Llama)│  │ API           │ │
│  │          │  │              │  │ (Image/Video)  │ │
│  │ Orquesta │  │ Piensa como  │  │ Genera media   │ │
│  │ todo     │  │ ella (local) │  │                │ │
│  └────┬─────┘  └──────┬───────┘  └────┬───────────┘ │
│       │               │               │              │
│  ┌────┴───────────────┴───────────────┴────────────┐ │
│  │              DATABASE / STATE                    │ │
│  │  Identities, Memory, Calendar, Analytics         │ │
│  └─────────────────────┬───────────────────────────┘ │
│                        │                             │
│  ┌─────────────────────┴───────────────────────────┐ │
│  │           SOCIAL APIs                            │ │
│  │  Instagram Graph API, TikTok API, Pinterest API  │ │
│  └──────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### LLM Local para Personalidad AI

| Opción | VRAM | Calidad | Deploy |
|--------|------|---------|--------|
| **Qwen3 14B** (recomendado) | 10GB | Muy buena, excelente en español/inglés | vLLM o Ollama |
| Llama 3.1 8B | 6GB | Buena para captions simples | Ollama |
| Llama 3.1 70B Q4 | 24GB | Excelente, casi cloud | vLLM en pod dedicado |
| Mistral 7B | 5GB | Buena, rápida | Ollama |

**Deploy recomendado:**
- **Opción A:** Ollama en el pod de imágenes (cuando Qwen imagen no está generando, liberar VRAM y cargar LLM)
- **Opción B:** Pod pequeño dedicado solo a LLM (GPU barata, A4000 16GB es suficiente)
- **Opción C:** CPU-only con Llama.cpp en cualquier server (sin GPU, más lento pero gratis)

**API local del LLM:**
```
POST http://localhost:11434/api/generate  (Ollama)
POST http://localhost:8000/v1/chat/completions  (vLLM, compatible con OpenAI format)
```

Mismo formato que OpenAI pero corriendo en tu pod. Tu engine no sabe la diferencia.
```

## Flujo completo de una publicación

```
1. Scheduler trigger → "Es hora de publicar para Mia"

2. Lovable Engine consulta:
   - Memory: ¿Qué publicó ayer? ¿Tiene campaña activa?
   - Calendar: ¿Hay algo planeado para hoy?
   - Trends: ¿Qué está trending en fitness?

3. LLM Local (con system prompt de Mia):
   - Input: "Genera el plan de contenido de hoy. Ayer publicaste sobre yoga. Tienes campaña de Gymshark activa."
   - Output: "Hoy quiero mostrar mi nueva colección Gymshark Vital Seamless haciendo sentadillas en el gym"

4. LLM Local genera prompt de imagen:
   - "Full body portrait, Mia (chestnut wavy hair, amber eyes, olive skin), doing goblet squat in modern gym, wearing sage green Gymshark Vital Seamless leggings and matching sports bra..."

5. i2i API genera imagen (T2I o I2I si usa imagen base)

6. LLM Local escribe caption:
   - "Obsessed with this new @gymshark Vital Seamless set 😍 The sage green is everything. Who else squats on Wednesdays? 🏋️‍♀️ #GymsharkVitalSeamless #LegDay #FitnessMotivation"

7. Lovable Engine publica via Instagram Graph API

8. AI monitorea engagement y responde comments
```

## Roadmap de implementación

| Fase | Qué | Timeline |
|------|-----|----------|
| **1** | Generar identidades base de 6 influencers | Ahora |
| **2** | Crear banco de 30+ imágenes por persona | Semana 1 |
| **3** | Definir personalidad AI y system prompts | Semana 1 |
| **4** | Crear cuentas de Instagram/TikTok | Semana 2 |
| **5** | Pipeline manual: AI genera, humano revisa y publica | Semana 2-4 |
| **6** | Pipeline semi-auto: AI genera y publica, humano supervisa | Mes 2 |
| **7** | Pipeline autónomo: AI opera sola con supervisión mínima | Mes 3+ |
| **8** | Engagement AI: responde comments automáticamente | Mes 3+ |
| **9** | Video content (I2V) integrado | Cuando pod video esté listo |
| **10** | Monetización: primer brand deal | Mes 4-6 |
