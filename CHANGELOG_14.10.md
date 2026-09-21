# CHANGELOG 14.10 — Nuvora API

**Fecha de cierre:** 21 de septiembre de 2026
**Estado:** ✅ COMPLETADA
**Tests:** 140 backend + 17 frontend = **157 nuevos** (14.10)
**Total proyecto:** 320 backend + 195 frontend = **515 tests**

---

## 🎯 Objetivo

Crear la **API pública oficial de Nuvora** para que cualquier usuario pueda consumir su bot desde aplicaciones, webs, automatizaciones o servicios externos mediante una **API Key**.

**Ciclo:** `crear bot → entrenar → workflow → IA → testear → PUBLICAR → generar API Key → consumir desde fuera`

---

## 🏗️ Principio arquitectónico

**La API es otro canal de entrada al Core existente.** No hay un segundo motor.

```

NUVORA CORE
│
┌────────────┼────────────┐
▼            ▼            ▼
Widget      Public API    Tester
│            │            │
└────────────┼────────────┘
▼
WorkflowEngine (14.5)

```

**Reutiliza:**
- `WorkflowEngine` (14.5) — motor único
- `public_sessions` (14.9) — sistema de sesiones
- `Conversation` con `channel="api"` — analytics
- `public_rate_limit` (14.9) — rate limiting

**Cero duplicación.**

---

## 📋 Subfases (14.10.1 → 14.10.12)

| # | Subfase | Trabajo |
|---|---|---|
| 14.10.1 | Auditoría + contrato | Diseño final validado contra código real |
| 14.10.2 | Modelo `ApiKey` + migración | Tabla + índices + `migrate_prod_14_10.py` |
| 14.10.3 | `ApiKeyService` | generate, hash, verify, create, list, revoke, resolve, touch |
| 14.10.4 | Schemas Pydantic | `ApiKeyCreate`, `ApiKeyResponse`, `ApiKeyCreatedResponse`, `ChatRequest`, `ChatResponse` |
| 14.10.5 | Dependencia `require_api_key` | Bearer auth + ApiKeyContext |
| 14.10.6 | Endpoints privados | `GET`/`POST`/`DELETE /bots/{bot_id}/api-keys` |
| 14.10.7 | **Endpoint público `POST /api/v1/chat`** | E2E con WorkflowEngine |
| 14.10.8 | Errores uniformes | Formato `{"error": {"code": "...", "message": "..."}}` |
| 14.10.9 | OpenAPI + documentación | Tags, ejemplos, responses documentadas |
| 14.10.10 | Frontend gestión de API Keys | Panel + modal crear |
| 14.10.11 | Tests E2E global | Ciclo completo end-to-end |
| 14.10.12 | Deploy + verificación prod | Render live + Aiven verificado |

---

## 🗄️ Modelo de datos

**Nueva tabla `api_keys`:**

```sql
id              INT PK
user_id         FK users (CASCADE) INDEX
bot_id          FK bots (CASCADE) INDEX
name            VARCHAR(100) NOT NULL
key_prefix      VARCHAR(30) INDEX
key_hash        VARCHAR(64) UNIQUE INDEX (SHA256)
created_at      TIMESTAMPTZ
last_used_at    TIMESTAMPTZ NULL
revoked_at      TIMESTAMPTZ NULL
expires_at      TIMESTAMPTZ NULL
is_active       BOOLEAN DEFAULT TRUE INDEX
```

Migración: backend/migrations/migrate_prod_14_10.py (idempotente)

---

🔑 Seguridad de API Keys

Capa Mecanismo
Generación secrets.token_urlsafe(32) → 256 bits entropía
Hash SHA256 hex (64 chars)
Verificación secrets.compare_digest (timing-safe)
Formato nvr_live_<43 chars base64url>
Almacenamiento Solo key_prefix + key_hash
Secreto completo UNA SOLA VEZ al crear
Revocación is_active=False + revoked_at (nunca se reactiva)

Formato de error uniforme:

```json
{
  "error": {
    "code": "INVALID_API_KEY",
    "message": "API Key is invalid."
  }
}
```

12 códigos: INVALID_API_KEY, REVOKED_API_KEY, EXPIRED_API_KEY, BOT_NOT_PUBLISHED, NO_ACTIVE_WORKFLOW, INVALID_REQUEST, MESSAGE_TOO_LONG, SESSION_NOT_FOUND, SESSION_EXPIRED, NOT_FOUND, RATE_LIMITED, INTERNAL_ERROR.

Formato clásico ({"detail": "..."}) preservado en /bots/*, /public/*, /workflows/*.

---

🌐 Endpoints

Públicos (Bearer API Key)

```
POST /api/v1/chat
```

Request:

```json
{
  "message": "Hola, ¿qué servicios ofrecéis?",
  "session_id": null
}
```

Response:

```json
{
  "answer": "¡Hola! 👋 ¿En qué puedo ayudarte?",
  "session_id": "abc-123-uuid",
  "status": "completed"
}
```

Privados (JWT)

```
GET    /bots/{bot_id}/api-keys
POST   /bots/{bot_id}/api-keys
DELETE /bots/{bot_id}/api-keys/{key_id}
```

---

🎨 Frontend

Fichero Rol
src/services/apiKeysApi.js Cliente HTTP de las 3 endpoints privadas
src/components/api-keys/ApiKeysPanel.jsx Panel lista + crear + revocar
src/components/api-keys/ApiKeyCreateModal.jsx Modal crear (muestra secret una vez)
src/pages/Dashboard.jsx Botón 🔑 API Keys en el sidebar

Funcionalidad:

· Lista de keys: nombre, prefix, fecha creación, último uso, estado
· Botón + Nueva API Key
· Al crear: muestra el secret UNA SOLA VEZ con botón copiar
· Botón 🗑 Revocar con confirmación
· Link 📚 Ver documentación de la API

---

🧪 Tests

Backend (140 tests nuevos)

Fichero Tests
test_api_key_model_14_10.py 11
test_api_key_service_14_10.py 21
test_api_key_schemas_14_10.py 17
test_api_auth_14_10.py 14
test_api_keys_router_14_10.py 17
test_api_v1_chat_14_10.py 19
test_api_errors_14_10.py 16
test_api_openapi_14_10.py 10
test_e2e_api_14_10.py 15
TOTAL 14.10 140

Frontend (17 tests nuevos)

Fichero Tests
apiKeysApi.test.js 3
ApiKeysPanel.test.jsx 14
TOTAL 17

Regresión completa: 320 backend + 195 frontend = 515 tests verdes.

---

🚀 Producción

Componente Estado
Backend https://nuvora-api-1hql.onrender.com — live con código 14.10
Frontend https://nuvora-chi.vercel.app — ready
Base de datos Aiven PostgreSQL Free (Amsterdam)
Deploy ID dep-daolsh80cd8s73e9tbhg

Verificación E2E en producción

· ✅ Health check OK
· ✅ OpenAPI tiene las 3 rutas API
· ✅ Frontend / y /login → 200
· ✅ Crear usuario + bot + workflow + publicar + API Key → OK
· ✅ POST /api/v1/chat sin key → 401 uniforme
· ✅ POST /api/v1/chat con key → respuesta del WorkflowEngine
· ✅ Segundo mensaje con session_id → contexto conservado
· ✅ Aiven tiene User + Bot + ApiKey + PublicSession + 2 Conversations (channel='api')
· ✅ Revocar key → 401 uniforme REVOKED_API_KEY
· ✅ Limpieza final: 0 filas en todas las tablas

La API está 100% funcional en producción end-to-end.

---

📚 Ejemplo de uso

```bash
curl https://nuvora-api-1hql.onrender.com/api/v1/chat \
  -H "Authorization: Bearer nvr_live_..." \
  -H "Content-Type: application/json" \
  -d '{"message": "Hola"}'
```

Respuesta:

```json
{
  "answer": "¡Hola! 👋 ¿En qué puedo ayudarte?",
  "session_id": "abc-123-uuid",
  "status": "completed"
}
```

Documentación interactiva: https://nuvora-api-1hql.onrender.com/docs

---

🚫 No incluido en 14.10 (futuro)

· ❌ SDK oficial (npm, Python)
· ❌ Webhooks
· ❌ OAuth
· ❌ Marketplace de integraciones
· ❌ Billing por API calls
· ❌ Dashboard avanzado de consumo
· ❌ Redis (14.13)
· ❌ API para administrar bots/workflows/conocimiento

14.10 se centra en: consumir un bot de Nuvora de forma segura mediante API.

---

🎯 Resultado final

Al terminar 14.10, Nuvora puede decir:

"Crea tu bot en Nuvora y conéctalo a cualquier aplicación mediante nuestra API."

```
MI WEB
   │
   │ Authorization: Bearer nvr_live_...
   ▼
NUVORA API
   │
   ▼
MI BOT
   │
   ▼
WORKFLOW ENGINE (14.5)
   │
   ▼
RESPUESTA
```

---

Próximo: 14.11 — Telegram
