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
