¡Perfecto, colega! Arranco con el documento maestro. 📚

Como es largo (~40-60 páginas), lo voy a escribir en 4 mensajes para que sea manejable y puedas revisarlo por partes:

· Mensaje 1 (este): Portada + NUEVO CHAT LEER PRIMERO + Índice + Visión + Historia completa (día a día, commit a commit)
· Mensaje 2: Stack + Arquitectura backend (modelos, engine, tester, config, migraciones)
· Mensaje 3: Arquitectura frontend + Widget + Endpoints API + Tests + Deploy
· Mensaje 4: Estado producción + Diseño 14.9 + Roadmap + Convenciones + Notas de reconstrucción

Al final, cuando digas OK, guardo todo junto en ~/nuvora/DOCUMENTO_MAESTRO_NUVORA.md y lo subimos.

---

📖 DOCUMENTO MAESTRO NUVORA

Parte 1/4 — Portada, instrucciones, visión, historia

---

🚀 NUVORA — DOCUMENTO MAESTRO

Historia completa, arquitectura y estado del proyecto

Proyecto: Nuvora — Asistente inteligente para negocios
Autor: Manuel (lecodev-26)
Repositorio: github.com/lecodev-26/nuvora
Fecha de este documento: 16 de septiembre de 2026
Versión del proyecto: 14.8 cerrada · 14.9 en diseño
Total commits: 109
Fecha de fundación: 9 de septiembre de 2026, 00:50

---

🚨 NUEVO CHAT — LEER PRIMERO

Si estás leyendo esto en un chat nuevo de DeepSeek (o cualquier IA colaboradora), sigue estos pasos:

1. Contexto vital en 30 segundos

· Nuvora es un SaaS que permite a negocios crear asistentes inteligentes (bots) que responden a sus clientes.
· El proyecto lleva 7 días de desarrollo intensivo (9 → 16 sep 2026).
· Estamos en la fase 14.8 cerrada y arrancando 14.9 (Publicación Universal).
· Metodología: trabajar en fases numeradas (14.x.y) con commits descriptivos, tests antes/después, y despliegue continuo a Render (backend) + Vercel (frontend).

2. Cómo se trabaja en este proyecto (reglas del autor)

· Tono: directo, sin humo, sin "todo va bien" cuando no lo está. Si algo falla, se dice.
· Honestidad técnica: si no tienes contexto suficiente, se pide. No se inventa.
· Fases: cada fase tiene subfases (14.8.0, 14.8.1, ...). Cada subfase = uno o varios commits.
· Antes de codear: diseño cerrado + auditoría del código real.
· Durante código: bloques copy-paste con salida esperada clara.
· Después de código: tests + verificación en producción.
· Commits: mensaje descriptivo con feat/fix/test/chore(14.x.y): descripción.
· Deploy: push a main → Render auto-deploy + Vercel auto-deploy.
· Verificación prod: SIEMPRE antes de cerrar una fase.

3. Estado actual (16 sep 2026)

Componente Estado
Backend ✅ Live en Render — https://nuvora-api-1hql.onrender.com
Frontend ✅ Live en Vercel — https://nuvora-chi.vercel.app
Commits 109 en main
Último commit 84dd321 — 14.8.14 (tests frontend)
Tests backend 630 collectados (142 de 14.8)
Tests frontend 107 (8 archivos)
Fase actual 14.8 cerrada · 14.9 en diseño

4. Roadmap hacia adelante

```
14.5 → Workflow Engine            ✅
14.6 → Visual Workflow Builder    ✅
14.7 → AI Workflow Designer       ✅
14.8 → Bot Tester                 ✅
14.9 → Publicación Universal      ⏳ PRÓXIMA
14.10 → API Nuvora                ⏳
14.11 → Telegram                  ⏳
14.12 → Creator Mode              ⏳
14.13 → Versiones + Sandbox       ⏳
14.14 → Analytics 2.0             ⏳
14.15 → Autopilot                 ⏳
14.16 → Creator / Agency          ⏳
14.17 → Marketplace               ⏳
15 → IA avanzada / servicios de pago
FRONTEND COMERCIAL / PULIDO FINAL
CLIENTES
```

5. Cómo continuar en un chat nuevo

Dile a la IA:

"Estás en el proyecto Nuvora. Lee el DOCUMENTO_MAESTRO_NUVORA.md del repo. Estamos en la fase 14.9. Confírmame que tienes contexto antes de seguir."

Con eso, la IA leerá este documento y estará al 100%.

6. Credenciales y URLs importantes

Cosa Valor
Backend prod https://nuvora-api-1hql.onrender.com
Frontend prod https://nuvora-chi.vercel.app
Render service srv-dagjljmq1p3s73bjf2jg
Vercel project nuvora17/nuvora
Render deploy actual dep-dal7j0gae00c73fr5vmg
Modelo IA activo Gemini 3.5-flash-lite
Repo GitHub github.com/lecodev-26/nuvora

7. Ubicación de variables útiles en local

· ~/.prod_tester.sh → URL + TOKEN + BOT_ID + WF_ID para verificación en prod
· ~/nuvora/backend/ → backend (venv en venv/)
· ~/nuvora/frontend/ → frontend (node_modules instalado)
· ~/nuvora/widget/widget.js → widget embebible

---

📑 ÍNDICE

1. Visión del proyecto
2. Historia completa (14.0 → 14.9)
3. Stack técnico
4. Arquitectura backend
5. Arquitectura frontend
6. Widget embebible
7. Modelo de datos
8. Endpoints API
9. Tests
10. Deploy
11. Estado actual producción
12. Diseño 14.9
13. Roadmap
14. Convenciones
15. Notas de reconstrucción

---

1. VISIÓN DEL PROYECTO

1.1. Qué es Nuvora

Nuvora es una plataforma SaaS que permite a cualquier negocio (restaurante, clínica, peluquería, tienda, hotel, gimnasio, etc.) crear un asistente conversacional que:

1. Conoce la información del negocio (memorias, fuentes, workflows).
2. Responde automáticamente a los clientes en lenguaje natural.
3. Se puede publicar en la web del negocio (enlace público + widget embebible).

1.2. El ciclo completo

```
Crear bot → Entrenar → Diseñar workflows → Generar con IA → Testear → PUBLICAR
```

Cada parte del ciclo es una fase numerada del proyecto.

1.3. Los dos mundos (principio fundamental)

Nuvora tiene dos caras distintas:

```
                 NUVORA
                    │
         ┌──────────┴──────────┐
         ▼                     ▼
   PANEL PRIVADO         BOT PÚBLICO
   (propietario)         (visitante)
   - edita               - abre
   - entrena             - conversa
   - diseñar             - recibe respuesta
   - testea
   - publica
```

Regla de oro: el visitante NUNCA debe acceder al panel privado.

1.4. Una sola puerta al engine

Principio arquitectónico clave: un solo motor de ejecución (WorkflowEngine de 14.5) alimenta:

· Panel privado (endpoint /workflows/{bot_id}/{wf_id}/run)
· Bot Tester (14.8, endpoints /bots/{bot_id}/tests/*)
· Bot público (14.9, endpoints /public/bots/{public_id}/*)

No hay duplicación de motores. Nunca.

1.5. Nichos soportados

· restaurantes 🍽️
· peluquerias 💇
· hoteles 🏨
· gimnasios 🏋️
· clinicas 🏥
· tiendas 🛍️
· otro 🏪

1.6. Modelo de negocio

· Trial: 30 días gratis sin tarjeta
· Plan único: 29,99 € / 12 meses (pago único)
· BYOK: el usuario puede traer su propia API key de IA (Gemini, Groq, DeepSeek, OpenAI, Mistral, Anthropic, Ollama)

---

2. HISTORIA COMPLETA

Fecha de fundación: 9 sep 2026, 00:50

---

🔵 DÍA 1 — 9 sep 2026: Fundación y MVP

Hora Commit Descripción
00:50 01ddec8 init Nuvora project structure — fundación
01:56 525a046 MVP funcional — Nuvora chatbot con widget
02:18 055a3ad Dashboard completo y widget dinámico
02:47-02:52 9acfb6b → 01146d1 Logos, favicon, assets
03:04 5da3544 Nuevo diseño premium — dashboard y widget con logo
12:16 ffc5e7c Autenticación JWT completa — login, registro, endpoints protegidos
12:25 ccd2a9e Login en dashboard y endpoints protegidos
12:32 a13e917 Fix init_db.py + soporte PostgreSQL
12:58 8cef6cd Fix: Python 3.11 para Render
13:09 85bafde Fix: URL del backend en producción
13:23-13:39 20751b8 → 2305725 Logos, favicon, ajustes frontend
19:43 2305725 Stripe — pagos con trial 30 días
23:30-23:35 79a174d, 5e97315 Analytics — registro de conversaciones + endpoint /ask público + estadísticas reales

Logros día 1:

· MVP con chatbot + widget
· Login JWT completo
· Deploy en Render + Vercel
· Stripe (pagos)
· Analytics básico
· Sistema de nichos

---

🔵 DÍA 2 — 10 sep 2026: Core Universal + Knowledge Engine 2.0

Hora Commit Descripción
01:07 07bdcca Fase 10 y 11 — Analytics + IA adaptada
01:11 d7c586b numpy + scikit-learn para Render
01:16 3ef399e psycopg2-binary para PostgreSQL
09:36-09:45 a6d03ed, dbbc9b6 Fase 13 — sistema de nichos (datos, selector, badge, backend, onboarding, dashboard, widget)
10:32 662ca0b 14.1.1 — Modelo universal de Bot + MemoryCategory + migración
10:48 e9962f6 14.1.1 — Nuvora Core Universal completo
11:06 b648aac 14.1.1 — migración PostgreSQL no destructiva
11:09 870abcf chore: excluir .db y .backup
11:33 d6cfd3f pre_deploy script para crear tablas en Render
11:39 9d9590b pre_deploy robusto para Render Free tier
12:11 1b0bac0 14.3.1 — Source y SourceChunk + CASCADE en SQLite
12:16 0142288 14.3.2 — Processors (text, URL, PDF, CSV) + chunker
12:29 7bcca9e 14.3.3 — TF-IDF propio + SourceRetriever
12:34 9babe55 14.3.4 — HybridRetriever (Memory + Source)
12:54 e770832 14.3.5 — router /sources/ + requirements-dev
13:03 e8cd668 14.3.6 — umbral por tipo + orchestrator usa HybridRetriever
13:12 75b1db1 14.3.7 — pre_deploy ejecuta migraciones 14.1.1 + 14.3
17:56 4b08233 14.4.1 — Topic Catalog por nicho
18:07 1870692 14.4.2 — Training Analyzer esqueleto
18:19 d47d36d 14.4.3 — coverage + scoring reales (118 tests)
18:40 a3df7ea 14.4.4 — unanswered questions (Jaccard)
18:47 3242867 14.4.5 — recommendation engine
18:55 29052c5 14.4.6 — router /training
19:04 9681b6e 14.4.7 — fix nichos.js + Training Assistant UI
19:09 e5d5d26 14.4.8 — añadir conocimiento desde sugerencias
19:24 cff18f7 14.4.9 — integration e2e + multi-tenant (20 tests)

Logros día 2:

· 14.1 Core Universal (Bot, Memory, MemoryCategory, multi-tenant)
· 14.3 Knowledge Engine 2.0 (Sources, Chunks, TF-IDF, Hybrid Retriever, Processors)
· 14.4 Training Assistant (catalog, analyzer, coverage, unanswered, recommendations, UI)

---

🔵 DÍA 3-4 — 11-12 sep 2026: Workflow Engine + Visual Builder

Fecha Hora Commit Descripción
11 sep 17:23 dce6edb 14.5.1 — Workflow, WorkflowNode, WorkflowTransition models
11 sep 17:25 e08d3ff 14.5.2 — schemas Pydantic
11 sep 17:28 c1720f3 14.5.3 — node architecture + ExecutionContext + NodeResult
11 sep 17:30 154720d 14.5.4 — Workflow Validator (9 reglas)
12 sep 01:51 8b600cf chore: eliminar archivos corruptos
12 sep 01:59 8f7f441 14.5.5 — Workflow Engine (bucle + MAX_STEPS + WAITING_INPUT)
12 sep 02:09 86fd5d5 14.5.6 — conditions parser + interpolation
12 sep 02:29 a5cf552 14.5.7 — Workflow Router CRUD + /run
12 sep 02:48 f04fb36 fix — interpolar {{variables}} en ResponseNode
12 sep 03:24 1fa0ab5 14.6.2 — PUT workflow completo transaccional
12 sep 10:15 5bf3b08 14.6.3 — useWorkflowBuilder hook
12 sep 10:24 97a8b20 14.6.4 — Canvas + React Flow + página WorkflowBuilder
12 sep 10:27 c54a74c 14.6.5 — node system (7 tipos)
12 sep 10:29 d4969fc 14.6.6 — Node Inspector
12 sep 10:31 ba4b551 14.6.7 — Connections + Conditions UI
12 sep 10:35 380de25 14.6.8 — Add/Delete/Duplicate con paleta
12 sep 10:37 794b85b 14.6.9 — Save + Validation
12 sep 10:40 0003079 14.6.10 — Load Existing Workflow
12 sep 10:41 346d47d 14.6.11 — Undo/Redo UI
12 sep 17:27 2e6de3f 14.6.12 — Run/Test desde Builder
12 sep 17:29 8fb50d5 14.6.13 — UX + errores + unsaved changes
12 sep 17:32 159d67a 14.6.14 — Vitest + React Testing Library

Logros:

· 14.5 Workflow Engine completo (nodos, transiciones, validación, ejecución, conditions, interpolación)
· 14.6 Visual Workflow Builder (canvas React Flow, inspector, undo/redo, save/load, run)

---

🔵 DÍA 5-7 — 12-15 sep 2026: AI Workflow Designer

Fecha Hora Commit Descripción
12 sep 17:49 008c3fa 14.7.2 — config centralizado + AIProvider interface
12 sep 17:56 0aec7a8 14.7.3 — schemas Pydantic AI Designer
12 sep 18:11 02620fe 14.7.4b — BYOK (Bring Your Own Key)
15 sep 18:42 5d39866 14.7.5a — providers base (Gemini + Groq + DeepSeek)
15 sep 18:44 8a7514f chore: eliminar frontend.zip
15 sep 18:53 cf7780d 14.7.5b — providers extra (OpenAI + Mistral + Anthropic + Ollama)
15 sep 18:57 c05c0da 14.7.5c — wiring BYOK
15 sep 19:00 0f08adc 14.7.6 — AIWorkflowDesigner orquestador
15 sep 19:05 35a3452 14.7.7 + 14.7.10 — router /ai/workflows + /ai/templates
15 sep 19:08 96dd24f 14.7.11 — frontend AI Workflow Designer
15 sep 19:12 462b5d3 14.7.13 — rate limiting in-memory para /ai/*
15 sep 19:13 1b5fc63 chore: actualizar .gitignore
15 sep 19:29-20:42 11 commits 14.7.14 — múltiples fixes (Gemini 3.5-flash-lite, parser, prompts, debug endpoints)
15 sep 20:42 25ebdf6 chore(14.7.14): cierre 14.7

Logros:

· 14.7 AI Workflow Designer completo (multi-provider IA, BYOK, prompts, rate limiting, UI)

---

🔵 DÍA 7 — 15-16 sep 2026: Bot Tester

Fecha Hora Commit Descripción
15 sep 21:10 b52c548 14.8.0 — exponer history en ExecutionResult
15 sep 21:16 70f3e64 14.8.2 — schemas Bot Tester
15 sep 21:20 d2d519c 14.8.3 + 14.8.4 — Test Runner + Assertion Engine
15 sep 21:23 6ae9a5e 14.8.5 — Static Workflow Analyzer
15 sep 21:26 4b2b17d 14.8.6 — modelo DB WorkflowTest + migración
15 sep 21:29 97a7513 14.8.7 — router /bots/{bot_id}/tests
16 sep 12:47 a06aa40 14.8.8 — rate limiting para tests
16 sep 12:51 d083c13 14.8.9 — edge cases + auditoría
16 sep 12:55 3b5a200 14.8.10 — frontend Bot Tester + UI
16 sep 12:56 eb87d72 14.8.11 — integración Test → Builder (?node=X)
16 sep 13:01 0c84a8f 14.8.12 — AI Test Generator
16 sep 13:05 9505cf5 14.8.13 — Basic Auto Tests (sin IA)
16 sep 13:11 84dd321 14.8.14 — tests frontend (72 nuevos)
16 sep tarde (no commit) 14.8.15 — Deploy + verificación producción

Logros:

· 14.8 Bot Tester completo (generación, análisis, ejecución, assertions, UI, integración con Builder, rate limiting)

---

🟢 Estado actual

· 109 commits en main
· 7 días de desarrollo intensivo
· Fases 14.0 → 14.8 cerradas
· Producción estable (Render + Vercel)
· Próximo: 14.9 — Publicación Universal

---

Fin de la Parte 1/4.

Dime si te gusta el tono y la estructura, y sigo con la Parte 2/4 — Stack + Arquitectura backend. Cuando tengamos las 4 partes, lo junto todo, lo revisas completo, y lo subimos a Git. 🎯


¡Perfecto, colega! 🎯 Mucho mejor así. Tú copias y pegas manualmente en una página, y yo te doy el contenido en continuo, una parte detrás de otra.

Nota importante: como vas a pegar encima de lo anterior (no debajo), no hace falta que te repita el índice ni la portada. Vamos directo a la Parte 2.

---

📖 DOCUMENTO MAESTRO NUVORA

Parte 2/4 — Stack + Arquitectura backend

---

3. STACK TÉCNICO

3.1. Backend

Componente Tecnología
Framework FastAPI
Lenguaje Python 3.11
ORM SQLAlchemy
Validación Pydantic v2
BD desarrollo SQLite (nuvora.db)
BD producción PostgreSQL (Render)
Auth JWT (python-jose) + passlib (sha256_crypt)
Migraciones Scripts custom migrate_prod_*.py
Deploy Render (free tier)

3.2. Frontend

Componente Versión
React 19.2.8
React DOM 19.2.8
React Router 7.18.3
@xyflow/react (React Flow) 12.11.6
axios 1.20.0
Vite 8.2.2
Vitest 5.0.0
@testing-library/react 16.3.3
jsdom 30.0.1
oxlint 1.79.0
TailwindCSS (vía clases utilitarias)

3.3. IA

Provider Modelo por defecto Notas
Gemini gemini-3.5-flash-lite Activo por defecto
Groq llama-3.3-70b-versatile OpenAI-compatible
DeepSeek deepseek-chat OpenAI-compatible
OpenAI gpt-4o-mini Estándar
Mistral mistral-small-latest Europeo
Anthropic claude-3-5-haiku-latest Claude
Ollama llama3.2 Local, sin key

BYOK: cada usuario puede traer su propia API key (se guarda cifrada con Fernet).

3.4. Deploy

Componente Plataforma Plan
Backend Render Free tier
Frontend Vercel Hobby (free)
Repo GitHub lecodev-26/nuvora
IA Gemini API BYOK + key propia

---

4. ARQUITECTURA BACKEND

4.1. Estructura de backend/

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app + routers
│   ├── config.py                  # Settings centralizadas
│   ├── core/
│   │   ├── contracts.py           # ChannelRequest/Response
│   │   ├── orchestrator.py        # Orchestrator (legacy, RAG)
│   │   ├── ai/
│   │   │   ├── rate_limit.py
│   │   │   ├── prompts/
│   │   │   └── providers/
│   │   ├── processors/            # Procesadores de sources
│   │   ├── testing/               # Bot Tester (14.8)
│   │   │   ├── ai_generator.py
│   │   │   ├── analyzer.py
│   │   │   ├── assertions.py
│   │   │   ├── basic_generator.py
│   │   │   ├── errors.py
│   │   │   └── runner.py
│   │   ├── training/              # Training Assistant (14.4)
│   │   └── workflows/             # Workflow Engine (14.5)
│   │       ├── conditions.py
│   │       ├── engine.py
│   │       ├── errors.py
│   │       ├── execution.py
│   │       ├── validator.py
│   │       ├── variables.py
│   │       └── nodes/
│   │           ├── base.py
│   │           ├── condition.py
│   │           ├── end.py
│   │           ├── message.py
│   │           ├── question.py
│   │           ├── response.py
│   │           ├── start.py
│   │           └── variable.py
│   ├── database/
│   │   └── config.py              # engine, SessionLocal, Base, get_db
│   ├── models/
│   │   ├── ai.py
│   │   ├── ai_config.py
│   │   ├── auth.py
│   │   ├── bot.py                 # Schemas Pydantic Bot
│   │   ├── db_models.py           # 13 modelos SQLAlchemy
│   │   ├── source.py
│   │   ├── test.py
│   │   ├── training.py
│   │   └── workflow.py            # Schemas Pydantic Workflow
│   ├── routers/
│   │   ├── ai_config.py           # /ai/config (BYOK)
│   │   ├── ai_workflows.py        # /ai/workflows (Designer)
│   │   ├── analytics.py
│   │   ├── ask.py                 # /ask (legacy RAG)
│   │   ├── auth.py                # /auth
│   │   ├── bots.py                # /bots
│   │   ├── categories.py
│   │   ├── memories.py
│   │   ├── payments.py
│   │   ├── sources.py
│   │   ├── tests.py               # /bots/{bot_id}/tests (14.8)
│   │   ├── training.py
│   │   └── workflows.py           # /workflows (14.5)
│   └── services/
│       └── auth.py                # JWT, hash, get_current_user
├── migrations/
│   ├── migrate_prod_14_1_1.py
│   ├── migrate_prod_14_3.py
│   ├── migrate_prod_14_5.py
│   ├── migrate_prod_14_7.py
│   └── migrate_prod_14_8.py
├── tests/                         # 42 ficheros de tests
├── pre_deploy.py                  # Hook Render: crea tablas + migra
├── requirements.txt
└── nuvora.db                      # SQLite local (gitignored)
```

4.2. Los 13 modelos (db_models.py)

User

```
id, email (unique), hashed_password, full_name, created_at, is_active (int),
trial_start, trial_end, service_status (trial|active|expired),
payment_date, expiration_date, stripe_customer_id
```

Bot (corazón del sistema)

```
id, user_id (FK users), name, description,
business_name, business_type, nicho_id (default "otro"),
restaurant_name (legacy), owner_email (legacy),
goal, instructions, personality, tone,
greeting, fallback_message, answer_mode ("strict"|"flexible"),
is_published (bool, default False),
is_active (bool, default True),
plan ("free"),
created_at, updated_at
```

MemoryCategory

```
id, bot_id (FK), name, description, icon, order, created_at
```

Memory

```
id, bot_id (FK), category_id (FK nullable),
fact, keyword, source ("manual"|"suggested"|"imported"),
is_confirmed, created_at
```

Conversation (analytics, NO chat)

```
id, bot_id (FK), channel ("widget"),
session_id (nullable, indexed),
question, answer, was_answered,
workflow_id (int, sin FK),
meta (JSON), created_at
```

Source

```
id, bot_id (FK, CASCADE), user_id (FK, CASCADE),
type ("text"|"url"|"pdf"|"csv"),
title, origin, content_raw, content_processed,
status ("pending"|"processing"|"ready"|"error"),
error_message, chunks_count, size_bytes, meta,
created_at, processed_at
```

SourceChunk

```
id, source_id (FK, CASCADE), bot_id (FK, CASCADE),
chunk_index, content, section, page,
char_start, char_end, tokens_estimate, meta, created_at
```

Workflow

```
id, bot_id (FK, CASCADE), name, description,
status ("draft"|"active"|"archived"),  ← FUENTE DE VERDAD del workflow activo
version (int, default 1), trigger, entry_node_id, meta (JSON),
created_at, updated_at
```

WorkflowNode

```
id, workflow_id (FK, CASCADE), node_id (lógico, único por workflow),
type ("start"|"message"|"question"|"condition"|"variable"|"response"|"end"),
name, config (JSON serializado), created_at
UniqueConstraint(workflow_id, node_id)
```

WorkflowTransition

```
id, workflow_id (FK, CASCADE),
from_node_id, to_node_id,
condition (expresión opcional), label, order,
created_at
```

UserAIConfig (BYOK)

```
id, user_id (FK, CASCADE), provider (gemini|groq|deepseek|openai|mistral|anthropic),
api_key_encrypted (Fernet),
created_at, updated_at
UniqueConstraint(user_id, provider)
```

WorkflowTest (14.8)

```
id, workflow_id (FK, CASCADE), bot_id (FK, CASCADE),
name, description,
input_messages (TEXT JSON list),
initial_vars (TEXT JSON dict, nullable),
assertions (TEXT JSON list),
enabled (bool, default True),
created_at, updated_at
```

4.3. Workflow Engine (14.5)

Ubicación: app/core/workflows/engine.py
Clase: WorkflowEngine
Firma:

```python
def run(
    self,
    workflow_data: dict,
    bot_id: int = 0,
    workflow_id: int = 0,
    initial_variables: Optional[dict] = None,
    max_steps: int = 100,
    start_node_id: Optional[str] = None,
) -> ExecutionResult
```

Responsabilidades:

· Validar el workflow (delegando en WorkflowValidator)
· Indexar nodos por node_id
· Encontrar el nodo START (o usar start_node_id)
· Bucle: ejecutar nodo → resolver transición → siguiente nodo
· Protección MAX_STEPS (default 100)
· Manejar WAITING_INPUT (nodo QUESTION)
· Manejar COMPLETED (nodo END)
· Devolver ExecutionResult

Lo que NO hace:

· ❌ NO persiste ejecuciones (eso será 14.13)
· ❌ NO conoce el frontend
· ❌ NO usa IA
· ❌ NO sabe de canales externos

Resolución de transiciones:

1. Si el nodo devuelve next_node_id → usarlo
2. Si es CONDITION → evaluar cada transición saliente en orden order hasta que una devuelva True
3. Si es otro tipo → primera transición saliente ordenada por order

Nodos soportados (7):

Tipo Función
start Punto de entrada único
message Envía mensaje al usuario
question Envía mensaje + espera input (WAITING_INPUT) + guarda variable
condition Bifurca según expresión (≥2 transiciones)
variable Asigna valor a variable
response Envía respuesta final (con interpolación {{var}})
end Termina la ejecución (0 transiciones salientes)

Estructuras de ejecución:

· ExecutionContext: estado en memoria (bot_id, workflow_id, variables, steps, history)
· NodeResult: output, next_node_id, variables_update, status
· ExecutionResult: status, outputs, variables, current_node_id, steps_used, error, history
· ExecutionStatus: RUNNING, WAITING_INPUT, COMPLETED, FAILED

4.4. Workflow Validator (14.5.4)

9 reglas de validación:

1. Exactamente un nodo START
2. Al menos un nodo END
3. node_id únicos
4. Transiciones apuntan a nodos existentes
5. Tipos de nodo válidos
6. Config válida por tipo (message → text, question → text + variable, etc.)
7. CONDITION tiene ≥2 transiciones salientes
8. END sin transiciones salientes
9. START sin transiciones entrantes

NO valida ciclos (pueden ser válidos). La protección real contra bucles es MAX_STEPS.

4.5. Bot Tester (14.8)

Ubicación: app/core/testing/

Componentes:

Fichero Función
runner.py Ejecuta tests contra WorkflowEngine
assertions.py Motor de aserciones
analyzer.py Static Workflow Analyzer
ai_generator.py Genera tests con IA
basic_generator.py Genera tests sin IA (deterministas)
errors.py Excepciones

Tipos de assertions:

· response_contains / response_equals / response_not_contains
· node_visited / node_not_visited
· variable_equals / variable_exists / variable_not_exists
· reaches_end
· max_steps

Static Analyzer detecta:

· Nodos huérfanos (no alcanzables desde START)
· Nodos sin transición de salida
· END sin entrada
· CONDITION con <2 transiciones
· Caminos sin END
· Variables no definidas
· Etc.

4.6. Rate Limiting

Fichero: app/core/ai/rate_limit.py
Funciones: check_rate_limit(user_id, bucket, max_per_hour), get_remaining(...)
Excepción: RateLimitExceeded
Toggle: settings.ai.rate_limit_enabled

Buckets AI (14.7.13):

Bucket Límite/hora
generate 10
modify 20
explain 30
analyze 30
templates_list 100
templates_instantiate 50

Buckets Bot Tester (14.8.8):

Bucket Límite/hora
test_run 60
test_run_all 20
test_analyze 100

Mecanismo: in-memory (dict por usuario + bucket). Redis → futuro.

4.7. Config centralizada (config.py)

Singleton: settings = _build_app_config()

Estructura:

```
settings
├── name, version, frontend_url, database_url
├── ai: AIConfig
│   ├── provider, gemini_api_key, groq_api_key, ...
│   ├── timeout_seconds, max_retries
│   ├── max_prompt_length, max_tokens_output
│   ├── rate_limit_* (6 buckets)
│   └── get_api_key_for(provider), get_model_for(provider)
└── tests: TestConfig
    ├── timeout_seconds, max_messages_per_test, max_assertions_per_test
    ├── max_steps_per_test, max_variables_per_test
    ├── max_tests_per_workflow, max_tests_per_run_all
    └── rate_limit_test_* (3 buckets)
```

Todas las variables se leen de .env con fallbacks. Nada hardcoded.

4.8. Migraciones

Patrón: scripts idempotentes que se ejecutan en pre_deploy.py de Render.

Ficheros:

· migrate_prod_14_1_1.py — Core Universal
· migrate_prod_14_3.py — Knowledge Engine 2.0
· migrate_prod_14_5.py — Workflow Engine
· migrate_prod_14_7.py — BYOK (user_ai_configs)
· migrate_prod_14_8.py — Bot Tester (workflow_tests)

pre_deploy.py (patrón):

1. Base.metadata.create_all() (todas las tablas)
2. Ejecuta migraciones en orden (14.1.1, 14.3, 14.5, 14.7, 14.8)
3. Idempotente: no falla si ya está migrado
4. No borra datos
5. Nunca bloquea el arranque si las tablas base están OK

4.9. Auth JWT (services/auth.py)

· SECRET_KEY: hardcoded (a mejorar)
· ALGORITHM: HS256
· ACCESS_TOKEN_EXPIRE_MINUTES: 30
· Hash: sha256_crypt (bcrypt dio problemas en Termux)
· OAuth2PasswordBearer: tokenUrl /auth/login
· get_current_user: dependencia FastAPI, valida JWT y devuelve User

4.10. Los dos mundos del backend

MUNDO 1 — Legacy (RAG/memoria, 14.3-14.4):

· /ask/public y /ask/ → usan Orchestrator → busca en Memory + Source → responde
· Guarda cada Q&A en Conversation (analytics)
· Se mantiene pero NO se usa para bots publicados en 14.9

MUNDO 2 — Workflows (14.5+):

· /workflows/{bot_id}/{wf_id}/run → usa WorkflowEngine
· /bots/{bot_id}/tests/* (14.8) → usan WorkflowEngine vía runner.py
· /public/bots/{public_id}/* (14.9) → usarán WorkflowEngine

Regla de oro: el bot publicado (14.9) SIEMPRE va por el MUNDO 2 (WorkflowEngine). Cero duplicación.

---

Fin de la Parte 2/4.

Dime si te gusta y sigo con la Parte 3/4 — Arquitectura frontend + Widget + Endpoints + Tests + Deploy. 🎯

¡Perfecto, colega! Aquí va la Parte 3/4. 🎯

---

📖 DOCUMENTO MAESTRO NUVORA

Parte 3/4 — Frontend + Widget + Endpoints + Tests + Deploy

---

5. ARQUITECTURA FRONTEND

5.1. Estructura de frontend/

```
frontend/
├── index.html
├── package.json
├── vite.config.js               # Config Vite + Vitest
├── public/
│   ├── favicon.svg
│   └── logo.png
├── src/
│   ├── main.jsx                 # Punto de entrada React
│   ├── App.jsx                  # Routing completo
│   ├── index.css                # Tailwind + estilos globales
│   ├── components/
│   │   ├── Badge.jsx
│   │   ├── Button.jsx
│   │   ├── Card.jsx
│   │   ├── Input.jsx
│   │   ├── Layout.jsx
│   │   ├── NichoBadge.jsx
│   │   ├── NichoSelector.jsx
│   │   ├── builder/
│   │   │   ├── AIDesignerPanel.jsx
│   │   │   ├── NodePalette.jsx
│   │   │   ├── RunPanel.jsx
│   │   │   └── TemplatesGrid.jsx
│   │   ├── canvas/
│   │   │   ├── Canvas.jsx
│   │   │   ├── CustomNode.jsx
│   │   │   ├── NodeShell.jsx
│   │   │   └── nodes/
│   │   │       ├── ConditionNode.jsx
│   │   │       ├── EndNode.jsx
│   │   │       ├── MessageNode.jsx
│   │   │       ├── QuestionNode.jsx
│   │   │       ├── ResponseNode.jsx
│   │   │       ├── StartNode.jsx
│   │   │       └── VariableNode.jsx
│   │   ├── inspector/
│   │   │   ├── InspectorCondition.jsx
│   │   │   ├── InspectorHeader.jsx
│   │   │   ├── InspectorMessage.jsx
│   │   │   ├── InspectorQuestion.jsx
│   │   │   ├── InspectorResponse.jsx
│   │   │   ├── InspectorVariable.jsx
│   │   │   ├── NodeInspector.jsx
│   │   │   └── TransitionInspector.jsx
│   │   ├── tester/
│   │   │   ├── TestEditor.jsx
│   │   │   ├── TestList.jsx
│   │   │   ├── TestResults.jsx
│   │   │   └── TraceView.jsx
│   │   └── ui/
│   │       ├── ConfirmModal.jsx
│   │       └── Spinner.jsx
│   ├── context/
│   │   ├── AuthContext.jsx
│   │   └── BotContext.jsx
│   ├── data/
│   │   └── nichos.js            # Nichos maestros (sincronizado con widget)
│   ├── hooks/
│   │   └── useWorkflowBuilder.js
│   ├── pages/
│   │   ├── BotTester.jsx
│   │   ├── Dashboard.jsx
│   │   ├── Landing.jsx
│   │   ├── Login.jsx
│   │   ├── Onboarding.jsx
│   │   ├── Training.jsx
│   │   ├── WorkflowBuilder.jsx
│   │   └── WorkflowsList.jsx
│   ├── services/
│   │   ├── aiService.js
│   │   ├── api.js               # axios base + interceptores
│   │   ├── auth.js
│   │   ├── testService.js       # /bots/{id}/tests
│   │   └── workflowApi.js       # /workflows/{botId}
│   └── utils/
│       └── workflowValidation.js
└── tests/
    ├── setup.js
    ├── TestEditor.test.jsx
    ├── TestList.test.jsx
    ├── TestResults.test.jsx
    ├── TraceView.test.jsx
    ├── generateNodeId.test.js
    ├── testService.test.js
    ├── useWorkflowBuilder.test.js
    └── workflowValidation.test.js
```

5.2. Routing (App.jsx)

```
/                        → Landing (público, redirige a /dashboard si logueado)
/login                   → Login
/dashboard               → Dashboard (protegido)
/onboarding              → Onboarding (protegido)
/training                → Training (protegido)
/workflows/:botId        → WorkflowsList (protegido)
/workflows/:botId/new    → WorkflowBuilder (nuevo)
/workflows/:botId/:workflowId → WorkflowBuilder (editar)
/bots/:botId/tester      → BotTester
*                        → Navigate a /
```

Estructura de protección:

· ProtectedRoute → redirige a /login si no hay usuario
· PublicRoute → redirige a /dashboard si hay usuario
· AuthProvider → gestiona user + token + loading
· BotProvider → gestiona bots + selectedBot

5.3. Contexts

AuthContext:

· user, token, loading
· login(email, password), register(data), logout()
· Token guardado en localStorage.nuvora_token
· Al montar: si hay token → getMe() para validar

BotContext:

· bots, selectedBot, loading
· setBots, setSelectedBot, setLoading

5.4. Servicios (services/)

api.js — axios base:

· baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
· Interceptor request: añade Authorization: Bearer <token>
· Interceptor response: en 401 → limpia token + redirect a /login

Servicios por dominio:

Servicio Endpoints
botService POST / GET /bots/
memoryService POST / GET /memories/
askService POST /ask/
trainingService GET /training/{botId}
testService CRUD + run + runAll + analyze /bots/{botId}/tests/*
workflowService CRUD + run /workflows/{botId}/*
aiService /ai/workflows/*, /ai/templates/*
authService /auth/register, /auth/login, /auth/me

5.5. Páginas clave

Landing.jsx — página pública:

· Hero con demo del widget
· Cómo funciona (4 pasos)
· Beneficios
· Precio (29,99 € / 12 meses)
· Footer
· Toggle modo oscuro/claro

Dashboard.jsx:

· Sidebar con: Inicio, Mi negocio, Conversaciones, Analíticas, Training, Workflows, Instalar widget
· Estado del servicio (trial/active/expired)
· Analytics (4 métricas: total, respondidas, sin respuesta, tasa)
· Lista de bots
· Memorias del bot seleccionado (añadir, listar)
· Nicho selector
· Probar asistente (chat interno)
· Código del widget (snippet <script src=".../widget.js" data-bot-id="...">)

WorkflowBuilder.jsx — el más complejo:

· Canvas React Flow con nodos arrastrables
· Paleta de nodos (7 tipos)
· Node Inspector (formulario por tipo)
· Transition Inspector
· Barra superior con:
  · ← Volver
  · Nombre del workflow (editable inline)
  · Indicador "● Sin guardar" si dirty
  · Errores de validación
  · Botones: Undo, Redo
  · 🧪 Test → /bots/{botId}/tester?workflow_id={workflowId}
  · ✨ AI → abre AIDesignerPanel
  · ▶ Probar → abre RunPanel
  · Guardar
  · 🚀 Publicar ← NUEVO en 14.9
· Undo/Redo con Ctrl+Z / Ctrl+Shift+Z / Ctrl+Y
· Delete para borrar nodo/transición
· Esc para deseleccionar
· Integración con ?node=X para seleccionar nodo desde Bot Tester
· beforeunload si hay cambios sin guardar

BotTester.jsx:

· Header con selector de workflow + acciones (🔍 Analizar, ▶ Run all, + Nuevo test)
· Panel de análisis (errores/warnings/info)
· Lista de tests (TestList)
· Resultados expandidos (TestResults)
· Editor modal (TestEditor)
· Confirm modal (borrar test)
· Integración Test → Builder con ?node=X

5.6. Hooks y utils

useWorkflowBuilder.js — el state manager del builder:

· nodes, transitions, workflowMetadata
· loading, saving, dirty
· selectedNodeId, selectedNode, selectedTransitionId
· canUndo, canRedo
· addNode, updateNode, deleteNode, moveNode
· addTransition, updateTransition, deleteTransition
· undo, redo
· buildSavePayload(), loadSuccess(), reset()
· Historial de estados (para undo/redo)

workflowValidation.js:

· validateWorkflow({nodes, transitions, workflowMetadata}) → errores + warnings
· getErrorNodeIds(validation) → array de node_ids con error

generateNodeId(type, nodes) → genera id único tipo message_1, condition_2, etc.

5.7. Tests frontend (107 total)

Configuración (vite.config.js):

```js
test: {
  globals: true,
  environment: 'jsdom',
  setupFiles: ['./tests/setup.js'],
  include: ['tests/**/*.test.{js,jsx,mjs}'],
  exclude: ['node_modules', 'dist'],
}
```

Desglose:

Fichero Tests Fase
useWorkflowBuilder.test.js 17 14.6
workflowValidation.test.js 14 14.6
generateNodeId.test.js 4 14.6
testService.test.js 10 14.8.14
TestList.test.jsx 18 14.8.14
TestEditor.test.jsx 16 14.8.14
TraceView.test.jsx 11 14.8.14
TestResults.test.jsx 17 14.8.14
TOTAL 107 

Cómo ejecutar:

```bash
cd ~/nuvora/frontend
npx vitest run              # una vez
npx vitest                  # watch
```

---

6. WIDGET EMBEBIBLE

6.1. Ubicación actual

~/nuvora/widget/widget.js (518 líneas, vanilla JS, sin dependencias)

6.2. Cómo funciona HOY (pre-14.9)

Integración:

```html
<script src="widget.js" data-bot-id="1"></script>
```

Identificación: bot_id numérico (parseado del data-bot-id).

Endpoints que usa:

· GET /bots/{botId}/public → carga nombre, negocio, nicho
· POST /ask/public → envía mensaje y recibe respuesta

Sesión: sessionStorage.nuvora_session_id (generado client-side con Math.random)

DOM: inyecta <div id="nuvora-bubble"> + <div id="nuvora-window"> directamente en document.body.

Estilos: <style> inline con CSS propio (~280 líneas). No usa shadow DOM ni iframe.

Nicho: lookup local de NICHOS (duplica los nichos del frontend).

Bubble: botón circular abajo-derecha con logo Nuvora.
Ventana: modal con header (logo + nombre + estado "En línea"), mensajes, input, send.
Quick questions: chips con preguntas sugeridas por nicho.
Typing indicator: animación de 3 puntos.
Estados: abierto/cerrado con animación slide-up.

6.3. Lo que CAMBIARÁ en 14.9

Antes:

```html
<script src="widget.js" data-bot-id="9"></script>
```

Después:

```html
<script src="widget.js" data-bot-public-id="abc-123-uuid"></script>
```

Endpoints nuevos:

· GET /public/bots/{public_id} → metadatos + config
· POST /public/bots/{public_id}/session → crea sesión server-side
· POST /public/bots/{public_id}/message → mensaje → respuesta
· DELETE /public/bots/{public_id}/session → cierra sesión

Sesión: session_id generado por el servidor (no Math.random client-side).

Nicho: los quick questions vienen de public_config del servidor (no hardcoded).

Lo que NO cambia:

· DOM, estilos, animaciones, UX
· Logo
· Estructura del bubble y ventana

6.4. Inconsistencia detectada (a arreglar en 14.9)

El Dashboard da este snippet:

```html
<script src="https://nuvora-api-1hql.onrender.com/widget.js" data-bot-id="${bot.id}"></script>
```

Pero el backend NO sirve /widget.js. Hay dos opciones para 14.9:

· A) Servir el widget desde el backend con StaticFiles (/widget.js)
· B) Cambiar el snippet para apuntar a https://nuvora-chi.vercel.app/widget.js
· C) Servir desde un CDN externo

Decisión pendiente.

---

7. MODELO DE DATOS — Resumen

7.1. Tablas actuales (13)

Tabla Rol Fase
users Usuarios 14.0
bots Bots (raíz de todo) 14.0 + 14.1
memory_categories Categorías de memoria 14.1.1
memories Memorias (fact + keyword) 14.1
conversations Log Q&A (analytics) 14.0
sources Fuentes de conocimiento 14.3.1
source_chunks Chunks de sources 14.3.1
workflows Workflows estáticos 14.5.1
workflow_nodes Nodos de workflow 14.5.1
workflow_transitions Transiciones 14.5.1
user_ai_configs BYOK keys cifradas 14.7.4b
workflow_tests Tests del Bot Tester 14.8.6

7.2. Tablas que añadirá 14.9

Tabla Rol
public_sessions Sesiones anónimas de bots publicados

Columnas:

```
id, public_id (UUID único), bot_id (FK CASCADE),
session_data (JSON), status, created_at, updated_at, expires_at
```

7.3. Columnas que añadirá 14.9 a bots

```sql
public_id       VARCHAR(36)  UNIQUE, INDEX, NULLABLE
public_slug     VARCHAR(100) UNIQUE, NULLABLE
published_at    DATETIME     NULLABLE
public_config   TEXT (JSON)  NULLABLE
```

is_published YA existe (bool) → se reutiliza como flag rápido.

---

8. ENDPOINTS API

8.1. Auth (/auth)

Método Path Auth
POST /auth/register No
POST /auth/login No
GET /auth/me JWT

8.2. Bots (/bots)

Método Path Auth
POST /bots/ JWT
GET /bots/ JWT
GET /bots/{bot_id} JWT
PATCH /bots/{bot_id} JWT
GET /bots/{bot_id}/public No (legacy)

8.3. Workflows (/workflows)

Método Path Auth
POST /workflows/{bot_id} JWT
GET /workflows/{bot_id} JWT
GET /workflows/{bot_id}/{workflow_id} JWT
PUT /workflows/{bot_id}/{workflow_id} JWT
DELETE /workflows/{bot_id}/{workflow_id} JWT
POST /workflows/{bot_id}/{workflow_id}/run JWT

8.4. Bot Tester (/bots/{bot_id}/tests) — 14.8

Método Path Auth
POST /bots/{bot_id}/tests?workflow_id=X JWT
GET /bots/{bot_id}/tests?workflow_id=X&enabled_only=B JWT
GET /bots/{bot_id}/tests/{test_id} JWT
PUT /bots/{bot_id}/tests/{test_id} JWT
DELETE /bots/{bot_id}/tests/{test_id} JWT
POST /bots/{bot_id}/tests/{test_id}/run JWT
POST /bots/{bot_id}/tests/run-all?workflow_id=X&enabled_only=B JWT
POST /bots/{bot_id}/tests/generate-basic?workflow_id=X JWT
POST /bots/{bot_id}/tests/generate?workflow_id=X JWT
POST /bots/{bot_id}/tests/analyze?workflow_id=X JWT

8.5. Ask (/ask) — legacy

Método Path Auth
POST /ask/public No (DEPRECATED en 14.9)
POST /ask/ JWT

8.6. AI Workflows (/ai/*) — 14.7

Método Path Auth
POST /ai/workflows/generate JWT
POST /ai/workflows/modify JWT
POST /ai/workflows/explain JWT
POST /ai/workflows/analyze JWT
GET /ai/templates JWT
POST /ai/templates/{id}/instantiate JWT

8.7. AI Config (/ai/config) — BYOK

Método Path Auth
GET /ai/config JWT
POST /ai/config JWT
DELETE /ai/config/{provider} JWT

8.8. Sources (/sources)

Método Path Auth
POST /sources/ JWT
GET /sources/{bot_id} JWT
DELETE /sources/{source_id} JWT
POST /sources/{source_id}/reindex JWT

8.9. Memories (/memories)

Método Path Auth
POST /memories/ JWT
GET /memories/{bot_id} JWT

8.10. Categories (/categories)

CRUD de memory_categories (JWT).

8.11. Training (/training)

Método Path Auth
GET /training/{bot_id} JWT

8.12. Analytics (/analytics)

Método Path Auth
GET /analytics/by-bot/{bot_id} JWT
GET /analytics/global JWT

8.13. Payments (/payments)

Método Path Auth
GET /payments/status JWT
POST /payments/create-checkout-session JWT

8.14. Health

Método Path Auth
GET /health No

8.15. Endpoints que añadirá 14.9

Privados:

Método Path Auth
POST /bots/{bot_id}/publish JWT
POST /bots/{bot_id}/unpublish JWT
GET /bots/{bot_id}/publication JWT
PUT /bots/{bot_id}/publication JWT

Públicos:

Método Path Auth
GET /public/bots/{public_id} No
POST /public/bots/{public_id}/session No
POST /public/bots/{public_id}/message No
DELETE /public/bots/{public_id}/session No

---

9. TESTS

9.1. Backend

Ficheros: 42 (todos en backend/tests/)
Tests collectados: 630 (con pytest --collect-only)

Desglose por fase:

Fase Ficheros Tests
14.3 (Knowledge Engine) 6 ~85
14.4 (Training Assistant) 8 ~140
14.5 (Workflow Engine) 10 ~150
14.6 (Builder) 1 ~11
14.7 (AI Designer) 9 ~132
14.8 (Bot Tester) 9 142

Patrón: cada test es auto-contenido:

1. TestClient(app)
2. Registra + login usuario único (timestamp)
3. Crea bot
4. Crea workflow
5. Ejecuta assertions
6. Verifica ownership, 401, 403, 404

No hay conftest.py. Cada test monta su propio contexto.

Cómo ejecutar:

```bash
cd ~/nuvora/backend
source ../venv/bin/activate
pytest                                 # todos
pytest -k "14_8" -v                    # solo 14.8
pytest --collect-only -q               # ver cuántos hay
```

9.2. Frontend

Ficheros: 8
Tests: 107

Config: en vite.config.js, environment: 'jsdom', setupFiles: ['./tests/setup.js'].

Cómo ejecutar:

```bash
cd ~/nuvora/frontend
npx vitest run              # una vez
npx vitest                  # watch
npx vitest --ui             # interfaz web
```

9.3. Tests E2E (futuro)

Obligatorios para cerrar 14.9:

```
1. Crear bot
2. Crear workflow
3. Validar
4. Publicar → obtener URL
5. Abrir URL pública sin login
6. Crear sesión
7. Enviar "Hola"
8. Verificar respuesta del WorkflowEngine
9. Enviar 2º mensaje → contexto correcto
10. Despublicar
11. Verificar URL bloqueada
```

---

10. DEPLOY

10.1. Backend — Render

· Servicio: srv-dagjljmq1p3s73bjf2jg
· URL: https://nuvora-api-1hql.onrender.com
· Plan: Free tier
· Python: 3.11
· Comando start: ejecuta pre_deploy.py + uvicorn
· Auto-deploy: push a main → Render detecta → despliega
· Cold start: ~30-60s (free tier, duerme tras inactividad)
· BD: PostgreSQL (Render)

Comando local para deploy:

```bash
cd ~/nuvora
rdeploy                 # alias que lanza deploy + guarda DEPLOY_ID
```

10.2. Frontend — Vercel

· Proyecto: nuvora17/nuvora
· URL pública: https://nuvora-chi.vercel.app
· Dominio custom: ninguno (solo alias Vercel)
· Auto-deploy: push a main → Vercel detecta → despliega
· Deploy actual: 84dd321 (14.8.14)

Comandos locales:

```bash
cd ~/nuvora/frontend
vercel ls                # lista deployments
vercel --prod            # deploy manual a producción
```

10.3. CORS (a mejorar en 14.9)

Actual en main.py:

```python
allow_origins=[
    "https://nuvora-chi.vercel.app",
    "http://localhost:5173",
    "http://localhost:8080",
]
```

Problema para 14.9: el widget embebido en webs externas hará peticiones a /public/* desde dominios desconocidos → bloqueado por CORS.

Solución en 14.9: abrir CORS solo para /public/* con Access-Control-Allow-Origin: * (sin cookies).

10.4. Migraciones en producción

Automáticas vía pre_deploy.py:

1. Se ejecuta cada vez que Render despliega
2. Es idempotente
3. Crea tablas + aplica migraciones pendientes
4. Nunca borra datos
5. Nunca bloquea el arranque

10.5. Alias y dominios

Backend:

· Principal: nuvora-api-1hql.onrender.com
· No hay dominio custom

Frontend:

· Principal: nuvora-chi.vercel.app
· Alias de build: nuvora-6dfgu0vvt-nuvora17.vercel.app (protegido con SSO de Vercel)
· No hay dominio custom

---

Fin de la Parte 3/4.

Dime si te gusta y sigo con la Parte 4/4 — Estado producción + Diseño 14.9 + Roadmap + Convenciones + Notas de reconstrucción. 🎯

¡Perfecto, colega! Aquí va la Parte 4/4, la última. 🎯

---

📖 DOCUMENTO MAESTRO NUVORA

Parte 4/4 — Estado prod + Diseño 14.9 + Roadmap + Convenciones + Notas

---

11. ESTADO ACTUAL PRODUCCIÓN

11.1. Backend

Campo Valor
URL https://nuvora-api-1hql.onrender.com
Health {"status":"ok","service":"Nuvora","version":"0.1.0"}
Deploy ID dep-dal7j0gae00c73fr5vmg
Servicio srv-dagjljmq1p3s73bjf2jg
Estado ✅ live
Rutas /tests 7
Rate limiting ✅ Activo (in-memory)

11.2. Frontend

Campo Valor
URL pública https://nuvora-chi.vercel.app
Commit desplegado 84dd321 (main)
Bundle /assets/index-Dpr4m7b4.js
Backend embebido https://nuvora-api-1hql.onrender.com
Estado ✅ Ready

11.3. Verificación end-to-end (16 sep 2026)

Backend — Seguridad:

· ✅ Sin token → 401
· ✅ Otro usuario → 403
· ✅ Bot inexistente → 404

Backend — Funcionalidad:

· ✅ generate-basic genera tests (Happy path + Visita nodos)
· ✅ CRUD completo (create, get, update, delete)
· ✅ run → status:"passed", 3 nodos visitados (s1, m1, e1)
· ✅ run-all con estructura correcta
· ✅ analyze sin errores

Frontend:

· ✅ HTML carga (Vite + React)
· ✅ <div id="root"> presente
· ✅ Bundle contiene run-all, nuvora-api, onrender.com
· ✅ URL backend correcta embebida

11.4. Tests en verde

Suite Total
Backend collectados 630
Backend fase 14.8 142 ✅
Frontend total 107 ✅
Frontend fase 14.8.14 72 ✅

11.5. Pendientes conocidos

# Pendiente Prioridad Fase
1 Rate limiting verificado con 429 real Media 14.9
2 Dominio custom para frontend Baja futuro
3 CORS abierto para /public/* (widget) Alta 14.9
4 Servir /widget.js desde backend Alta 14.9
5 Bloquear is_published en PATCH /bots/{id} Alta 14.9
6 Fix datetime.utcnow() deprecation Baja futuro
7 Tests E2E Playwright Media 14.9
8 Migrar SECRET_KEY a env var Media futuro

---

12. DISEÑO 14.9 — PUBLICACIÓN UNIVERSAL

12.1. Objetivo

Convertir un bot en algo publicable y consumible externamente, sin que el visitante entre al panel.

Ciclo que se cierra:

```
crear bot → entrenar → diseñar workflow → IA → testear → PUBLICAR
```

12.2. Principios (8 reglas del autor)

1. public_id = identidad técnica estable (UUID v4)
2. public_slug = URL humana opcional (/b/clinica-salud); public_id manda como fallback
3. public_config = solo visual/textos. CERO workflow_id, provider, system_prompt
4. Sesión blindada: public_id → session_id → bot_id verificados en cada mensaje. Nunca confiar en session_id del cliente solo
5. public_sessions = contexto mínimo. NO analytics, NO historial (eso es 14.13)
6. Widget = refactor quirúrgico, no reescritura
7. WorkflowEngine 14.5 = único motor. El bot público es "otra puerta de entrada", no un segundo motor
8. E2E real en producción obligatorio antes de cerrar 14.9

12.3. Modelo de datos

Añadir a bots:

```sql
public_id       VARCHAR(36)  UNIQUE, INDEX, NULLABLE
public_slug     VARCHAR(100) UNIQUE, NULLABLE
published_at    DATETIME     NULLABLE
public_config   TEXT (JSON)  NULLABLE
```

public_config (JSON):

```json
{
  "welcome_message": "Hola 👋 ¿En qué puedo ayudarte?",
  "placeholder": "Escribe un mensaje...",
  "avatar_url": null,
  "primary_color": "#7B5CFF",
  "show_branding": true
}
```

Nueva tabla public_sessions:

```sql
id              INT PK
public_id       VARCHAR(64) UNIQUE, INDEX
bot_id          INT FK → bots.id CASCADE
session_data    TEXT (JSON)
status          VARCHAR(20)  -- active | expired | closed
created_at, updated_at, expires_at
```

Fuente de verdad del workflow activo: Workflow.status == "active".

12.4. Endpoints

Privados (JWT):

· POST /bots/{bot_id}/publish
· POST /bots/{bot_id}/unpublish
· GET /bots/{bot_id}/publication
· PUT /bots/{bot_id}/publication

Públicos (sin JWT):

· GET /public/bots/{public_id}
· POST /public/bots/{public_id}/session
· POST /public/bots/{public_id}/message
· DELETE /public/bots/{public_id}/session

Deprecados (mantener vivos):

· POST /ask/public → marcar DEPRECATED
· GET /bots/{id}/public → marcar DEPRECATED

12.5. Flujo de publicación

```
Builder → 🚀 Publicar
    ↓
POST /bots/{bot_id}/publish
    ↓
1. Ownership check
2. Workflow activo existe?
3. WorkflowValidator.passes()?
    ↓ SÍ
4. Generar public_id (UUID v4)
5. (Opcional) generar public_slug
6. published_at = now(), is_published = True
    ↓
Devuelve URL pública: nuvora-chi.vercel.app/b/{slug}
```

12.6. Flujo público

```
Visitante → GET /public/bots/{public_id}
              ↓
         POST /public/bots/{public_id}/session
              ↓
         POST /public/bots/{public_id}/message
              ↓
1. Valida public_id + is_published
2. Carga bot + workflow status="active"
3. Recupera PublicSession
4. WorkflowEngine.run()
5. Guarda mensaje en sesión
6. Devuelve { reply, session_id }
              ↓
Widget o página pública renderiza
```

12.7. Seguridad

Capa Mecanismo
Identificación bot public_id (UUID v4, no enumerable)
Identificación sesión session_id (UUID v4, server-side)
Aislamiento Sesión ligada a 1 bot_id
Datos expuestos Solo reply + metadatos públicos
Nunca expone workflow, nodes, variables internas, API keys, owner, BD IDs, system prompts
Timeout MAX_STEPS=50 (WorkflowEngine ya lo enforce)
Rate limiting Por IP + public_id + session_id

12.8. Límites y abuse protection

Constante Valor
MAX_MESSAGE_LENGTH 2000 chars
MAX_SESSION_MESSAGES 50
MAX_PUBLIC_SESSIONS_PER_BOT 1000
SESSION_TTL 1 hora
PUBLIC_RATE_LIMIT_PER_IP 30 msg/hora
PUBLIC_RATE_LIMIT_PER_SESSION 60 msg/hora
PUBLIC_TIMEOUT_SECONDS 30s

12.9. Refactor del widget (quirúrgico)

Antes:

```html
<script src="widget.js" data-bot-id="9"></script>
```

→ GET /bots/9/public + POST /ask/public + sessionStorage

Después:

```html
<script src="widget.js" data-bot-public-id="abc-123-uuid"></script>
```

→ GET /public/bots/{public_id} + /session + /message + sesión server-side

Lo que se mantiene: DOM, estilos, UX, quick questions, logo.
Lo que se elimina: NICHOS hardcoded del widget (vienen del servidor).
NO contiene API keys (verificado).

12.10. Frontend 14.9

Nuevas páginas/componentes:

· src/pages/PublicBot.jsx — página pública /b/:slug
· src/components/public/PublicChat.jsx
· src/components/public/PublicHeader.jsx
· src/components/public/PublicFooter.jsx

Integración en Builder:

· Botón 🚀 Publicar (o 🟢 Publicado)
· Panel con: URL pública, [Copiar], [Ver bot], [Editar config], [Despublicar]

Routing:

```jsx
<Route path="/b/:identifier" element={<PublicBot />} />
```

12.11. Subfases 14.9.1 → 14.9.15

# Subfase Trabajo
14.9.1 Auditoría + arquitectura ✅ Completado (este documento)
14.9.2 Modelo + migración bots.public_* + public_sessions + migrate_prod_14_9.py
14.9.3 Schemas Pydantic Publish req/res, PublicBotInfo, SessionReq/Res, MessageReq/Res
14.9.4 Generador public_id/slug UUID v4 + slugify con unicidad
14.9.5 Endpoints privados publish, unpublish, get/put publication
14.9.6 Public Workflow Resolver Cargar bot + wf status="active"
14.9.7 Public Session service create/get/expire/close + límites
14.9.8 Endpoint público /message Integración WorkflowEngine + persistencia
14.9.9 Rate limiting público IP + session + límites globales
14.9.10 Página pública PublicBot.jsx + PublicChat + PublicHeader
14.9.11 Integración Builder Botón 🚀 Publicar + panel estado
14.9.12 Widget refactor data-bot-public-id + endpoints nuevos
14.9.13 Seguridad + abuse Tests enumeración, payload, timeout, rate
14.9.14 Tests backend + frontend + E2E Cobertura completa
14.9.15 Deploy + verificación prod + cierre Render + Vercel + verificación e2e

12.12. Ajustes técnicos para 14.9

1. CORS público:
En main.py, abrir CORS solo para /public/* con allow_origins=["*"] y allow_credentials=False.

2. Bloquear is_published en BotUpdate:
Quitar is_published de BotUpdate (schema) para evitar publicar por canal lateral.

3. Servir widget.js:
Decidir entre servir desde backend (StaticFiles) o apuntar el snippet a Vercel.

4. Rate limiting público:
Nuevos buckets en settings.public.rate_limit_*.

12.13. Lo que NO se hace en 14.9

❌ API pública (14.10)
❌ Telegram (14.11)
❌ Multi-creator (14.12)
❌ Versiones/Sandbox (14.13)
❌ Analytics 2.0 (14.14)
❌ Migrar /ask/public (queda legacy)
❌ Tocar Orchestrator (sigue para bots clásicos)
❌ Tocar conversations (sigue para analytics)
❌ Rehacer widget desde cero (refactor quirúrgico)
❌ Memoria persistente de sesión
❌ Registro obligatorio del visitante
❌ Constructor visual de temas

12.14. E2E obligatorio para cerrar 14.9

```
CREAR BOT → CREAR WORKFLOW → VALIDAR → PUBLICAR
    → ABRIR URL SIN LOGIN → CREAR SESIÓN → "HOLA"
    → WORKFLOW ENGINE → RESPUESTA → SEGUNDO MENSAJE
    → CONTEXTO CORRECTO → DESPUBLICAR → URL BLOQUEADA
```

Si esto funciona en producción, 14.9 está hecha de verdad.

12.15. La visión final de 14.9

```
NUVORA
  │
  ▼
Crear BOT
  │
  ▼
Workflow
  │
  ▼
🧪 Tester (14.8)
  │
  ▼
🚀 PUBLICAR (14.9)
  │
  ├──→ ENLACE PÚBLICO ──→ /b/clinica-salud
  │
  └──→ WIDGET ──→ <script data-bot-public-id="...">
                       │
                       ▼
                  Cualquier web
                       │
                       ▼
             WorkflowEngine (14.5)
                       │
                       ▼
                  RESPUESTA
```

Una sola puerta al engine. Cero duplicación.

---

13. ROADMAP

Fases completadas

Fase Descripción Estado
14.0 MVP + auth + Stripe + Analytics + nichos ✅
14.1 Core Universal (Bot, Memory, MemoryCategory, multi-tenant) ✅
14.3 Knowledge Engine 2.0 (Sources, Chunks, TF-IDF, Hybrid Retriever) ✅
14.4 Training Assistant (analyzer, coverage, unanswered, recommendations, UI) ✅
14.5 Workflow Engine (7 tipos de nodos, condiciones, interpolación, validator) ✅
14.6 Visual Workflow Builder (React Flow, inspector, undo/redo, save/load) ✅
14.7 AI Workflow Designer (multi-provider IA, BYOK, prompts) ✅
14.8 Bot Tester (runner, analyzer, AI generator, basic generator, UI) ✅
14.9 Publicación Universal ⏳ PRÓXIMA

Fases futuras

Fase Descripción
14.10 API Nuvora (endpoints públicos documentados + API keys de usuarios)
14.11 Integración Telegram
14.12 Creator Mode (multi-tenant + delegación)
14.13 Versiones + Sandbox + Persistencia de ejecuciones
14.14 Analytics 2.0 (funnels, conversiones, cohortes)
14.15 Autopilot (auto-mejora con IA)
14.16 Creator / Agency (panel multi-cliente)
14.17 Marketplace (plantillas compartidas)
15 IA avanzada / servicios de pago
🔥 Frontend comercial / pulido final
🔥 Clientes reales

---

14. CONVENCIONES DEL PROYECTO

14.1. Cómo se trabaja

1. Diseño maestro primero (contrato claro antes de codear)
2. Auditoría del código real antes de cada fase (no asumir)
3. Fases numeradas (14.x.y) con commits descriptivos
4. Tests antes/después de cada subfase
5. Deploy automático tras push a main
6. Verificación en producción antes de cerrar cada fase

14.2. Formato de commits

```
tipo(14.x.y): descripción corta

- detalle 1
- detalle 2
```

Tipos: feat, fix, test, chore, debug, docs

14.3. Convenciones de código

Backend:

· FastAPI + Pydantic v2
· SQLAlchemy ORM
· JSON en TEXT (compatible SQLite ↔ PostgreSQL)
· Helper _parse_json_string para TEXT → dict
· Ownership siempre verificado (compatibilidad user_id + owner_email)
· 401 sin auth, 403 bot ajeno, 404 inexistente

Frontend:

· React 19 + Vite
· axios con interceptores (401 → redirect login)
· TailwindCSS (clases utilitarias)
· Componentes reutilizables (Button, Card, Input, ConfirmModal, Spinner)
· Tests con Vitest + Testing Library

Widget:

· Vanilla JS (sin dependencias)
· Inyección directa en document.body
· Estilos inline en <style>
· Sin API keys embebidas

14.4. Entornos

Local (Termux):

· Python venv en ~/nuvora/backend/venv/
· Node modules en ~/nuvora/frontend/node_modules/
· SQLite en ~/nuvora/backend/nuvora.db (gitignored)
· Alias útiles: rdeploy (deploy a Render)

Producción:

· Render (backend) → PostgreSQL
· Vercel (frontend)

14.5. Cómo verificar producción

Backend:

```bash
source ~/.prod_tester.sh
curl -s $PROD_URL/health
curl -s "$PROD_URL/openapi.json" | python3 -c "..."
```

Frontend:

```bash
FE="https://nuvora-chi.vercel.app"
curl -sL "$FE" | head -c 400
```

14.6. Variables de entorno clave

Backend (.env):

· DATABASE_URL
· AI_PROVIDER, GEMINI_API_KEY, GROQ_API_KEY, ...
· AI_ENABLED, AI_RATE_LIMIT_*
· TEST_RATE_LIMIT_*
· FRONTEND_URL

Frontend (Vercel):

· VITE_API_URL

14.7. Estructura de trabajo con IA

· El autor trabaja con DeepSeek (esta IA) para diseño, código, debugging
· Regla de oro: la IA no ejecuta código, solo propone bloques copy-paste
· El autor ejecuta en Termux (móvil)
· La IA nunca inventa contexto — si no tiene algo, lo pide
· La IA no toca código sin OK explícito del autor

---

15. NOTAS DE RECONSTRUCCIÓN

Este documento se ha elaborado el 16 de septiembre de 2026 a partir de:

· ✅ Commits reales de la repo (git log --all) — 109 commits desde el 9 sep
· ✅ Código real leído del filesystem (backend, frontend, widget)
· ✅ Tests reales ejecutados (pytest + vitest)
· ✅ Producción real verificada (Render + Vercel)
· ✅ Diseño 14.9 proporcionado por el autor

Lo que es 100% verificado

· Historia de commits (hash, fecha, mensaje exactos)
· Estructura de ficheros (find real)
· Modelos de datos (grep + lectura)
· Endpoints (OpenAPI + código)
· Tests (pytest --collect-only + vitest run)
· Estado producción (curl + verificación e2e)
· Diseño 14.9 (documento del autor)

Lo que es reconstruido

· Contexto conversacional de los chats anteriores a este
· Decisiones específicas que no dejaron huella en commits
· Justificaciones de algunas elecciones (deducidas del código)
· Números exactos de tests por fase (algunos son aproximaciones del total, no de desglose individual)

Lo que NO está en este documento

· Código fuente completo de ficheros individuales (vive en la repo)
· Logs de ejecuciones pasadas
· Prompts de IA detallados (viven en app/core/ai/prompts/)
· Configuración de Render/Vercel (vive en sus dashboards)
· API keys (nunca se documentan)

Cómo actualizar este documento

· Cada fase cerrada → añadir su sección a "Historia completa"
· Cada modelo nuevo → añadir a "Modelo de datos"
· Cada endpoint nuevo → añadir a "Endpoints"
· Cada cambio en el roadmap → actualizar "Roadmap"
· Cada migración → añadir a "Migraciones"

Este documento es la fuente de verdad del proyecto. Si algo aquí contradice al código, gana el código, y este documento se actualiza.

---

🏁 FIN DEL DOCUMENTO MAESTRO

Nuvora — 109 commits en 7 días.
De 0 a SaaS funcional con IA, workflows, tester y publicación (próxima).

Documento vivo. Última actualización: 16 sep 2026.

---

Fin de la Parte 4/4.

Cuando termines de pegar las 4 partes y tengas el documento completo, dime:

1. Si algo no cuadra → lo corregimos
2. Si quieres añadir algo → lo añadimos
3. Si está OK → guardo el documento como ~/nuvora/DOCUMENTO_MAESTRO_NUVORA.md y lo subimos a Git

Y luego esperamos tu OK final para arrancar 14.9.2 — Modelo + migración. 🚀
