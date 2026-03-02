# Proyecto: Agente Autónomo Real con LangGraph

## La idea

Quiero construir un agente autónomo **de verdad** — no un chatbot con herramientas, no un wrapper de API, no una demo de hackathon. Un sistema que pueda recibir una tarea compleja, descomponerla, ejecutarla paso a paso durante horas o días, recuperarse de fallos, buscar soluciones cuando no sabe algo, y comunicarse conmigo si hay una emergencia real.

Esto no es un proyecto personal cerrado. Tiene que ser **open source y multipropósito**: cualquier persona con una computadora modesta y acceso a modelos gratuitos debe poder levantarlo y tener un agente funcional. La autonomía computacional no es un privilegio de quien paga Claude a $20/mes.

---

## Lo que aprendí rompiendo OpenClaw

Vengo de una sesión de 8 horas auditando OpenClaw v2026.2.23. Lo que descubrí:

### Bugs reales encontrados

- **SSRF guard bloquea localhost**: el agente no podía acceder a SearXNG local porque `ssrf.ts` bloquea `localhost` como IP privada. Fix: agregar `browser.ssrfPolicy.allowedHostnames: ["localhost"]`
- **Mem0 crashea con `<think>` tags**: MiniMax M2.1 genera `<think>...</think>` en respuestas JSON internas. El plugin `mem0ai@2.2.1` hace `JSON.parse()` directo y explota con `SyntaxError: Unexpected token '<'`
- **Mezcla de idiomas**: MiniMax escribió `comunicación和工作 language` (español + chino) en un JSON interno
- **`text.replace is not a function`**: bug upstream en el plugin de Mem0 — recibe un objeto donde espera un string
- **Subagentes fallan silenciosamente**: timeouts 4/4, tools invocados sin parámetros (`read` sin `path`), sin logging visible para el usuario
- **Sin auto-failover**: si el modelo principal cae, el agente se queda colgado. No hay retry con otro modelo
- **Sesiones efímeras**: cada conversación muere al terminar. No hay persistencia de tareas entre sesiones

### Modelos testeados en NVIDIA NIM (gratis)

| Modelo                                | Think tags | JSON limpio   | Veredicto               |
| ------------------------------------- | ---------- | ------------- | ----------------------- |
| `deepseek-ai/deepseek-v3.2`           | ❌ NO      | ✅ SÍ         | **MEJOR opción gratis** |
| `meta/llama-3.3-70b-instruct`         | ❌ NO      | ✅ SÍ         | Buen fallback           |
| `minimaxai/minimax-m2.1`              | ✅ SÍ      | ❌ NO         | Roto para tool calling  |
| `nvidia/llama-3.3-nemotron-super-49b` | ✅ SÍ      | ❌ NO         | Think tags en JSON      |
| `qwen/qwen3-235b-a22b`                | —          | Error/timeout | No disponible           |

### Conclusión

OpenClaw es un **asistente reactivo disfrazado de agente autónomo**. Sirve para chat + tools manuales, pero no tiene persistencia real, no se recupera de fallos, y la "autonomía" es 90% marketing.

---

## Principios de diseño del nuevo sistema

### 1. Model-agnostic de verdad

Tiene que funcionar desde el modelo más chiquito (Llama 3.2 3B en una notebook) hasta el más grande (DeepSeek V3.2 685B en la nube). La arquitectura no puede asumir que el modelo es inteligente — tiene que compensar las limitaciones del modelo con estructura, prompts adaptativos, y validación de outputs.

Si un modelo chico no puede hacer tool calling nativo, el sistema tiene que **parsear texto libre** y extraer las intenciones. Si un modelo grande puede hacer structured output, que lo use. La inteligencia está en el grafo, no solo en el modelo.

### 2. Resourcefulness (ingeniárselas)

Si el agente no sabe cómo hacer algo, no se queda parado. Tiene que:

- **Buscar cómo hacerlo**: consultar SearXNG, leer documentación, buscar ejemplos
- **Aprender skills dinámicamente**: si necesita generar una imagen y no tiene tool, buscar una API gratuita, probarla, y usarla
- **Escalar al humano cuando es necesario**: si todo falla, notificar al usuario por el canal más efectivo disponible

### 3. Comunicación de emergencia

Si el agente detecta una situación crítica (un proceso destruyendo archivos, un servicio caído que necesita atención urgente, un deadline que se pasa), tiene que poder:

- Mandar notificación por terminal/desktop
- Si tiene mi número y acceso a una API de TTS + llamadas VoIP gratuita (ej: Twilio free tier, o Google Cloud TTS + SIP), **llamarme al celular** y decirme qué pasa con voz sintetizada
- Si no tiene cómo llamar, mandar mail, webhook, lo que sea — **encontrar la forma**

### 4. Interfaz

No es un script de terminal que escupe logs. Necesita una interfaz:

- **Web dashboard** liviana (FastAPI + HTMX, o similar — sin frameworks pesados de JS)
- Visualización del grafo en tiempo real: qué nodo se está ejecutando, cuál completó, cuál falló
- Timeline de eventos: cada tool call, cada decisión, cada error — todo visible
- Control: poder pausar, resumir, cancelar, y forzar re-ejecución de un nodo
- Estado de los modelos: cuál está activo, latencia, rate limits restantes

### 5. Persistencia real

- **Checkpointing SQLite**: el estado completo del grafo se guarda en cada transición
- **Resume**: si se cae la luz, el proceso, o el modelo, retoma exactamente donde quedó
- **Memoria entre sesiones**: un SQLite separado con hechos aprendidos del usuario y del contexto, sin depender de plugins npm rotos
- **Time-travel**: poder volver a cualquier paso anterior, ver qué datos tenía, y re-ejecutar desde ahí

### 6. Auto-failover de modelos

```
Intento 1: deepseek-ai/deepseek-v3.2 (NVIDIA NIM)
  ↓ timeout/rate-limit/error
Intento 2: meta/llama-3.3-70b-instruct (NVIDIA NIM)
  ↓ timeout/rate-limit/error
Intento 3: modelo local via Ollama (si hay uno cargado)
  ↓ todo falló
Acción: notificar al usuario, pausar tarea, guardar checkpoint
```

---

## Infraestructura disponible

### Hardware

```
CPU:       AMD Ryzen 7 5700U (8c/16t, sin GPU dedicada)
RAM:       16GB DDR4
Disco:     SSD
SO:        Arch Linux (systemd, pacman)
Red:       Internet domiciliaria estándar
```

### Servicios locales funcionando

| Servicio | Puerto                 | Función                                      |
| -------- | ---------------------- | -------------------------------------------- |
| SearXNG  | http://localhost:8080  | Meta search engine local, API JSON           |
| Ollama   | http://127.0.0.1:11434 | Embeddings (mxbai-embed-large, 1024 dims)    |
| OpenClaw | http://127.0.0.1:18789 | Asistente reactivo (coexiste, no reemplazar) |

### APIs gratuitas

```
NVIDIA NIM:
  URL:     https://integrate.api.nvidia.com/v1
  Key:     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
  Format:  OpenAI-compatible
  Modelos: deepseek-v3.2 (principal), llama-3.3-70b (fallback)
  Límite:  ~40 req/min
```

### Herramientas del sistema

- Python 3.x (pacman, usar venv)
- pnpm (para frontend si hace falta)
- Git
- Neovim
- Brave Browser

---

## Restricciones absolutas

1. **CERO costos** — solo APIs gratis y modelos locales
2. **Sin Docker** — Python venv directo (mi máquina no tiene RAM de sobra para containers)
3. **Sin frameworks JS pesados** — nada de React/Next.js/Vue para la interfaz. HTMX, Alpine.js, o vanilla JS máximo
4. **Código legible y documentado** — esto se publica open source
5. **Español argentino** en toda la interfaz y comunicación del agente
6. **No depender de un solo modelo ni proveedor** — tiene que sobrevivir si NVIDIA NIM se cae mañana

---

## Test de validación (definición de "funciona")

### Test 1: Tarea multi-step con checkpointing

> "Investigá las diferencias entre State Space Models y Transformers. Armá un análisis técnico y guardalo en un archivo. Si se te corta internet a mitad, que pueda retomar."

Debe: buscar en SearXNG → analizar → escribir archivo → checkpoint en cada paso → poder resumir si se interrumpe.

### Test 2: Auto-failover de modelo

Desconectar NVIDIA NIM a mitad de tarea. El agente debe detectar el error, cambiar a Ollama local o al modelo fallback, y continuar.

### Test 3: Resourcefulness

> "Generame un diagrama de flujo de la arquitectura y guardalo como imagen."

El agente NO tiene tool de generación de imágenes. Debe: buscar cómo generar diagramas programáticamente → encontrar Mermaid/Graphviz/etc → instalarlo → generar el diagrama → guardarlo.

### Test 4: Comunicación de emergencia

Simular un proceso que está borrando archivos importantes. El agente debe: detectar la anomalía → intentar frenar el proceso → notificar al usuario por el medio más efectivo disponible.

---

## Lo que NO es este proyecto

- No es otro wrapper de ChatGPT
- No es un juguete de hackathon
- No es una demo que funciona solo en el video de YouTube
- No es exclusivo para programadores — tiene que tener interfaz

**Es un sistema autónomo real que se las ingenia con lo que tiene, aprende de sus errores, y sirve para cualquier persona. Open source. Gratis. Multipropósito.**

---

## Contexto personal

Mi nombre de usuario es qu4ntum. Trabajo en proyectos de IA independientes:

- **ConciencIA**: motor de inferencia en C puro para modelos Qwen (reemplazo de PyTorch)
- **Integral Dynamics**: investigación en procesos transformadores universales

Prefiero Rust > Python para proyectos nuevos. Uso pnpm > npm. Mi API de NVIDIA NIM vence el 15/03/2026. Siempre hablame en español argentino.
