# CHANGELOG 14.12 — Creator Mode

**Fecha de cierre:** 24 de septiembre de 2026
**Estado:** ✅ COMPLETADA
**Tests:** 20 backend + 20 frontend = **40 nuevos** (14.12)
**Total proyecto:** ~380 backend + ~246 frontend

---

## 🎯 Objetivo

Convertir Nuvora en una **experiencia coherente de creación de bots**.

Creator Mode NO añade funcionalidad nueva. **Orquesta** las existentes en un **Creator Workspace por bot**.

**Ciclo:**
`CREAR → PROBAR → LANZAR`

---

## 🏗️ Principio arquitectónico

**Un bot = un espacio de creación.**

Todas las rutas de un bot viven bajo `/bots/:botId/*`.

```

NUVORA
│
├── Mis bots
│
└── MI BOT
│
├── CREAR
│   ├── Configuración
│   ├── Conocimiento
│   └── Flujos
│
├── PROBAR
│   ├── Training
│   └── Tester
│
└── LANZAR
├── Publicación
└── Canales

```

**Reutiliza:**
- WorkflowEngine (14.5)
- Tester (14.8)
- Publication (14.9)
- API Keys (14.10)
- Telegram (14.11)
- ChannelRequest/Response (14.3)
- WorkflowValidator (14.5.4)

**Cero duplicación. Sin nuevas migraciones.**

---

## 📋 Subfases (14.12.1 → 14.12.25)

| # | Subfase | Trabajo |
|---|---|---|
| 14.12.1 | Auditoría Creator Experience | Inventario + análisis |
| 14.12.2 | Diseño final Creator Workspace | Arquitectura + contrato |
| 14.12.3 | **Backend `creator-status`** | Endpoint + servicio + 20 tests |
| 14.12.4 | CreatorLayout + Sidebar + Header | Shell |
| 14.12.5 | Rutas `/bots/:botId/*` + legacy redirects | App.jsx refactor |
| 14.12.6 | Migración de enlaces internos | ~10 enlaces |
| 14.12.7 | Hook `useCreatorStatus` | Fetch + cache ligero |
| 14.12.8 | BotOverviewCard + BotReadiness | Componentes overview |
| 14.12.9 | SetupChecklist + NextStepCard | Estado + next step |
| 14.12.10 | EmptyState + CreatorError | Componentes reutilizables |
| 14.12.11 | CreatorOverview funcional | Overview completo |
| 14.12.12 | CreatorConfig con tabs | Básico / Personalidad / Comportamiento |
| 14.12.13 | CreatorKnowledge con tabs | Memorias + Fuentes + Categorías |
| 14.12.14-15 | Workflows + Training + Tester | Integrados vía CreatorLayout (sin wrappers) |
| 14.12.16 | CreatorChannels + CreatorPublication | Wrappers de paneles existentes |
| 14.12.17 | BotsList (nuevo /dashboard) | Selector de bots |
| 14.12.18 | Responsive móvil | Drawer + tabs scroll |
| 14.12.19 | Backend tests | Incluidos en 14.12.3 |
| 14.12.20 | Frontend tests | 20 tests |
| 14.12.21 | Regression | 26 archivos frontend + backend Telegram/Creator |
| 14.12.22 | Deploy + verificación | Render live + endpoint OK |
| 14.12.23 | E2E Creator journey | 8 pasos verificados |
| 14.12.24 | UX + Security audit | 7 checks OK |
| 14.12.25 | CHANGELOG + auditoría final | Este documento |

---

## 🗄️ Modelo de datos

**Sin migración.**

Creator Mode es **puramente orquestación frontend + 1 endpoint agregado**.

**Reutiliza todos los modelos existentes:**
- Bot, Memory, Source, MemoryCategory
- Workflow, WorkflowNode, WorkflowTransition
- WorkflowTest
- ApiKey
- TelegramIntegration
- PublicSession

---

## 🔌 Endpoint nuevo

### `GET /bots/{bot_id}/creator-status`

**Auth:** JWT obligatorio.
**Ownership:** verificado (404/403).

**Contrato definitivo (minimalista):**

```json
{
  "bot_id": 3,
  "configuration": { "ok": true },
  "workflow": { "ok": true, "id": 5, "name": "WF Principal" },
  "publication": { "ok": true, "public_url": "https://..." },
  "channels": { "web": true, "api": false, "telegram": true },
  "ready": true,
  "next_step": null
}
```

7 claves. Sin puntuaciones. Sin datos internos. Determinista.

---

✅ Definición de READY

```
READY = configuration.ok AND workflow.ok AND publication.ok
```

NO exige:

· ❌ Knowledge (memorias / fuentes)
· ❌ Tests
· ❌ API Keys
· ❌ Telegram
· ❌ Nicho específico (nicho_id=null es VÁLIDO)

Verificado: los caminos oficiales de Widget, API y Telegram usan WorkflowEngine + get_active_workflow. Eso es READY.

---

🎯 Reglas deterministas de next_step

```
if not configuration.ok → "configuration"
elif not workflow.ok    → "workflow"
elif not publication.ok → "publication"
else                    → None
```

Sin IA. Sin puntuaciones. Sin lógica por nicho.

Nota sobre workflow.ok: reutiliza WorkflowValidator (14.5.4). NO hay segunda validación paralela.

---

📊 Canales

Modelo: channels = { web, api, telegram }

Canal Cuándo es true
web bot.is_published && bot.public_id (activado al publicar)
api Existe ≥1 ApiKey activa no revocada no expirada
telegram Existe TelegramIntegration status="connected" y activa

Ningún canal adicional es requisito de READY.

---

🎨 Frontend

Estructura nueva:

```
src/
├── pages/
│   ├── BotsList.jsx              ← NUEVO /dashboard
│   └── creator/
│       ├── CreatorOverview.jsx
│       ├── CreatorConfig.jsx
│       ├── CreatorKnowledge.jsx
│       ├── CreatorChannels.jsx
│       └── CreatorPublication.jsx
│
├── components/creator/            ← NUEVO
│   ├── CreatorLayout.jsx
│   ├── CreatorSidebar.jsx
│   ├── CreatorHeader.jsx
│   ├── BotOverviewCard.jsx
│   ├── BotReadiness.jsx
│   ├── SetupChecklist.jsx
│   ├── NextStepCard.jsx
│   ├── EmptyState.jsx
│   └── CreatorError.jsx
│
├── hooks/
│   └── useCreatorStatus.js        ← NUEVO
│
└── services/
    └── sourcesApi.js              ← NUEVO
```

Rutas:

```
/dashboard                        → BotsList (selector)
/onboarding                       → Crear bot
/bots/:botId                      → CreatorOverview
/bots/:botId/config               → CreatorConfig
/bots/:botId/knowledge            → CreatorKnowledge
/bots/:botId/workflows            → WorkflowsList
/bots/:botId/workflows/new        → WorkflowBuilder
/bots/:botId/workflows/:wfId      → WorkflowBuilder
/bots/:botId/training             → Training
/bots/:botId/tester               → BotTester
/bots/:botId/publication          → CreatorPublication
/bots/:botId/channels             → CreatorChannels
```

Legacy redirects (mantener hasta 14.14):

```
/training?bot_id=X → /bots/X/training
/workflows/:botId  → /bots/:botId/workflows
```

---

🧪 Tests

Backend (20 nuevos):

Fichero Tests
test_creator_status_14_12.py 20

Cubre: auth 401, 404, 403, config OK/KO, workflow 0/1 válido/1 inválido/2+, publication OK/KO, channels web/api/telegram, ready, next_step (4 reglas), no filtración.

Frontend (20 nuevos):

Fichero Tests
useCreatorStatus.test.jsx 3
CreatorLayout.test.jsx 3
BotOverviewCard.test.jsx 5
BotReadiness.test.jsx 3
NextStepCard.test.jsx 3
EmptyStateCreatorError.test.jsx 3

Regresión: 26 archivos frontend verdes + 40 tests Telegram + 20 tests Creator backend.

---

🚀 Producción

Componente Estado
Backend https://nuvora-api-1hql.onrender.com — live
Endpoint creator-status ✅ Funcionando
Frontend /dashboard ✅ BotsList
Frontend /bots/:botId ✅ CreatorWorkspace

Verificación E2E en producción (8 pasos):

· ✅ Registro + login
· ✅ Crear bot → next_step: workflow
· ✅ Crear workflow + activar → next_step: publication
· ✅ Publicar → next_step: null, ready: true
· ✅ Bot "desde cero" (nicho_id=null) es válido
· ✅ Canales adicionales (API/Telegram) son opcionales
· ✅ Multitenancy → 403
· ✅ Security audit 7/7 OK

---

🚫 No incluido en 14.12

· ❌ Rediseño comercial completo (fase posterior)
· ❌ Nueva IA
· ❌ Marketplace
· ❌ Creator/Agency
· ❌ Colaboración multiusuario
· ❌ Equipos
· ❌ Billing nuevo
· ❌ Stripe nuevo
· ❌ WhatsApp, Discord
· ❌ Redis
· ❌ Autopilot
· ❌ Versionado / Sandbox
· ❌ Nueva base de conocimiento
· ❌ Nuevo Workflow Engine
· ❌ Rediseño de tests existentes
· ❌ Subida de PDF/URL/CSV desde CreatorKnowledge (fase futura)

---

🎯 Resultado final

Al terminar 14.12, Nuvora puede decir:

"Crea tu bot. CREA → PRUEBA → LANZA. Todo en un solo lugar."

Experiencia coherente: el usuario entra a un bot y no salta entre aplicaciones.

Navegación por bloques mentales: CREAR / PROBAR / LANZAR.

Estado claro en todo momento: qué está OK, qué falta, qué hacer ahora.

Sin gamificación. Sin IA innecesaria. Sin duplicación.

---

Próximo: 14.13 — Redis / Rate Limiting

Migrar el rate limiting a Redis para soportar multi-instancia.

Y en paralelo se puede ir preparando 14.14 — Analytics 2.0.

---

Fin del CHANGELOG 14.12
