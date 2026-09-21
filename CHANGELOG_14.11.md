# CHANGELOG 14.11 — Telegram Channel

**Fecha de cierre:** 22 de septiembre de 2026
**Estado:** ✅ COMPLETADA
**Tests:** 40 backend + 26 frontend = **66 nuevos** (14.11)
**Total proyecto:** ~360 backend + 221 frontend (aislados)

---

## 🎯 Objetivo

Demostrar que Nuvora es una **plataforma multicanal real**:
Telegram entra como **Channel Adapter**, NO como motor paralelo.

**Ciclo:**
`crear bot → entrenar → workflow → IA → testear → PUBLICAR → conectar Telegram → chatear desde Telegram`

---

## 🏗️ Principio arquitectónico

**Telegram es OTRO canal de entrada al Core existente.** Cero duplicación.

```

┌── Widget
│
├── API
│
├── Tester
│
└── Telegram ──► TelegramAdapter ──► ChannelRequest
↓
NUVORA CORE
↓
WorkflowEngine
↓
ChannelResponse
↓
TelegramAdapter
↓
Telegram

```

**Reutiliza:**
- `ChannelRequest` / `ChannelResponse` (14.3)
- `WorkflowEngine` (14.5) — motor único
- `public_sessions` (14.9) — sistema de sesiones multicanal
- `Conversation` con `channel="telegram"` — analytics
- `encrypt_api_key` / `decrypt_api_key` (14.7) — cifrado de token
- `public_rate_limit` (14.9) — rate limiting

**Cero duplicación.**

---

## 📋 Subfases (14.11.1 → 14.11.24)

| # | Subfase | Trabajo |
|---|---|---|
| 14.11.1 | Estructura `channels/` | `ChannelAdapter` base (Protocol) |
| 14.11.2 | Modelo `TelegramIntegration` + `TelegramUpdate` | Migración 14.11 |
| 14.11.3 | `public_sessions` multicanal | +channel +external_id (migración 14.11.3) |
| 14.11.4 | `TelegramClient` | getMe, setWebhook, deleteWebhook, sendMessage |
| 14.11.5 | `TelegramAdapter` (mapper) | Update → ChannelRequest |
| 14.11.6 | `TelegramAdapter` (send) | ChannelResponse → sendMessage |
| 14.11.7 | `TelegramService` | connect, disconnect, status, test |
| 14.11.8 | Router privado JWT | `/bots/{id}/telegram/*` |
| 14.11.9 | Webhook público | `POST /webhooks/telegram/{secret}` |
| 14.11.10 | Tests formales webhook | 20 tests |
| 14.11.11 | Rate limiting Telegram | 2 buckets nuevos |
| 14.11.12 | Tests sesión multicanal | 10 tests |
| 14.11.13 | Frontend service | `telegramApi.js` |
| 14.11.14 | Frontend panel | `TelegramPanel` + `TelegramConnectModal` |
| 14.11.15 | Frontend Dashboard | Sección "Canales" + `ChannelsPanel` |
| 14.11.16 | Tests frontend 1 | 12 tests (api + modal) |
| 14.11.17 | Tests frontend 2 | 14 tests (panel + channels) |
| 14.11.18 | Verificación backend | Regresión (deuda descubierta) |
| 14.11.19 | Tests integración E2E | 10 tests |
| 14.11.20 | Regresión frontend | 221 tests verdes |
| 14.11.21 | Deploy Render | `pre_deploy.py` ampliado + migraciones en Aiven |
| 14.11.22 | E2E real Telegram | Bot @minuvorabot conectado + mensaje real |
| 14.11.23 | Verificación producción | Webhook info + logs |
| 14.11.24 | Auditoría final | Documento maestro actualizado |

---

## 🗄️ Modelo de datos

**Nueva tabla `telegram_integrations`:**

```sql
id                  INT PK
bot_id              FK bots (CASCADE) UNIQUE INDEX
telegram_bot_id     VARCHAR(50)
telegram_username   VARCHAR(100)
encrypted_token     TEXT (cifrado BYOK)
webhook_secret      VARCHAR(64) UNIQUE INDEX
webhook_url         VARCHAR(500)
status              VARCHAR(20) ("pending" | "connected" | "error" | "disconnected")
is_active           BOOLEAN DEFAULT TRUE
created_at          TIMESTAMPTZ
updated_at          TIMESTAMPTZ
last_event_at       TIMESTAMPTZ NULL
last_error          TEXT NULL
```

Nueva tabla telegram_updates (idempotencia):

```sql
id                  INT PK
integration_id      FK telegram_integrations (CASCADE) INDEX
update_id           BIGINT NOT NULL
created_at          TIMESTAMPTZ DEFAULT now()

UNIQUE(integration_id, update_id)
```

Modificación public_sessions:

```sql
+ channel       VARCHAR(20) NOT NULL DEFAULT 'widget' INDEX
+ external_id   VARCHAR(100) NULL INDEX
```

Migraciones: migrate_prod_14_11.py + migrate_prod_14_11_3.py (idempotentes)

---

🔐 Seguridad

Capa Mecanismo
Token Telegram Cifrado con encrypt_api_key (mismo que BYOK 14.7)
Token expuesto NUNCA se devuelve por API (solo token_configured: bool)
Webhook secret secrets.token_urlsafe(32) (~43 chars)
Webhook - URL /webhooks/telegram/{secret}
Webhook - Header X-Telegram-Bot-Api-Secret-Token
Webhook - Validación Ambos deben coincidir → 403 si no
Idempotencia UNIQUE(integration_id, update_id) → INSERT atómico
Rate limiting 120/integración + 240/IP por minuto
Ownership Verificado en todos los endpoints privados (JWT)
Bot no publicado Fallback al usuario en Telegram
Sin workflow activo Fallback al usuario en Telegram
Fallo del engine Fallback al usuario en Telegram (nunca rompe webhook)

Formato de error uniforme: solo en /api/v1/* (formato clásico en el resto).

Errores propios de Telegram:

· TelegramError (base)
· TelegramAuthError (token inválido)
· TelegramAPIError (error de Telegram)
· TelegramNetworkError (timeout/red)
· TelegramIntegrationError (negocio)
· TelegramAlreadyConnectedError (ya conectado)
· TelegramNotConnectedError (sin integración)

Mapeo a HTTP:

· TelegramAlreadyConnectedError → 409
· TelegramNotConnectedError → 404
· TelegramAuthError → 400
· TelegramAPIError → 502
· TelegramNetworkError → 504

---

🌐 Endpoints

Privados (JWT):

```
GET    /bots/{bot_id}/telegram                → estado actual
POST   /bots/{bot_id}/telegram/connect        → conectar (getMe + setWebhook + cifrado)
POST   /bots/{bot_id}/telegram/test           → probar conexión (getMe con token guardado)
POST   /bots/{bot_id}/telegram/disconnect     → desconectar (deleteWebhook + marcar inactivo)
```

Público (webhook secret):

```
POST   /webhooks/telegram/{webhook_secret}
```

Request (de Telegram):

```json
{
  "update_id": 123456789,
  "message": {
    "message_id": 42,
    "date": 1726934400,
    "chat": {"id": 111, "type": "private"},
    "from": {"id": 111, "is_bot": false, "first_name": "Juan"},
    "text": "Hola"
  }
}
```

Response:

```json
{"ok": true, "status": "processed"}
```

Códigos posibles de respuesta:

· 200 {ok: true, status: "processed"} → procesado
· 200 {ok: true, ignored: "duplicate"} → idempotencia
· 200 {ok: true, ignored: "not_processable"} → grupo/sin texto/bot
· 200 {ok: true, status: "bot_not_published"} → bot no publicado
· 200 {ok: true, status: "no_workflow"} → sin workflow activo
· 403 → secret inválido
· 404 → integración no encontrada
· 429 → rate limit excedido

Regla de oro de webhooks: siempre 200 (salvo secret inválido), rápido, nunca filtrar detalles internos.

---

🎨 Frontend

Fichero Rol
services/telegramApi.js Cliente HTTP de los 4 endpoints privados
components/channels/TelegramPanel.jsx Panel con estado + conectar/probar/desconectar
components/channels/TelegramConnectModal.jsx Modal con instrucciones BotFather + input token
components/channels/ChannelsPanel.jsx Vista global de canales (Web/API/Telegram/WhatsApp-Discord futuros)
pages/Dashboard.jsx Botón "📡 Canales" en sidebar + render ChannelsPanel

UX:

· Panel desconectado: borde dashed cyan + "Conectar Telegram"
· Panel conectado: borde verde + badge "🟢 Conectado" + @username + fechas + "Probar"/"Desconectar"
· Modal: instrucciones paso a paso + input tipo password + aviso "el token se cifra"

NUNCA se muestra el token ni el webhook_secret.

---

🧪 Tests

Backend (40 tests):

Fichero Tests
test_telegram_webhook_14_11.py 20
test_public_session_telegram_14_11.py 10
test_telegram_integration_14_11.py 10
TOTAL 40

Frontend (26 tests):

Fichero Tests
telegramApi.test.js 6
TelegramConnectModal.test.jsx 6
TelegramPanel.test.jsx 7
ChannelsPanel.test.jsx 7
TOTAL 26

Cobertura:

· Seguridad: secret inválido, integración inactiva, ownership
· Idempotencia: mismo update_id, distintos, entre integraciones
· Filtrado: sin texto, grupo, bot, no-JSON
· Multitenancy: 2 bots, mismo chat
· Estados: no publicado, sin workflow
· Analytics: channel=telegram, sesión creada
· Rate limiting: 429 tras muchas peticiones
· E2E: flujo completo + multi-turno + expiración

⚠️ Nota sobre suite completa: la suite backend completa mantiene ~29 fallos pre-existentes por contaminación entre archivos (ver Deuda 11 del documento maestro). Los tests de 14.11 pasan aislados.

---

🚀 Producción

Componente Estado
Backend https://nuvora-api-1hql.onrender.com — live con código 14.11
Frontend https://nuvora-chi.vercel.app — ready
Base de datos Aiven PostgreSQL Free (Amsterdam)
Migraciones 14.11 + 14.11.3 aplicadas vía pre_deploy.py
Bot Telegram @minuvorabot (conectado en producción)

Verificación E2E en producción:

· ✅ Health check OK
· ✅ OpenAPI tiene las 5 rutas Telegram
· ✅ Crear usuario + bot + workflow + publicar → OK
· ✅ Conectar Telegram → OK (getMe + setWebhook con HTTPS)
· ✅ getWebhookInfo → URL correcta + pending_update_count: 0
· ✅ Mensaje real "Hola" enviado desde móvil
· ✅ Respuesta real recibida: "¡Hola desde Nuvora + Telegram! 🚀"
· ✅ last_event_at actualizado
· ✅ last_error: null
· ✅ Múltiples mensajes → respuestas independientes (multi-turno OK)

La integración Telegram está 100% funcional en producción end-to-end.

---

🏆 Hito arquitectónico

Añadir Telegram NO requirió tocar:

· ❌ Core
· ❌ WorkflowEngine
· ❌ ChannelRequest / ChannelResponse
· ❌ Contratos universales

Solo se creó un Adapter que traduce formatos.

Esto confirma que la arquitectura universal de Nuvora funciona.
La próxima vez que se añada WhatsApp o Discord, el proceso será idéntico.

---

⚠️ Notas sobre deuda técnica

Descubierta en 14.11.18: la suite backend completa tiene ~29 fallos por contaminación entre archivos (comparten nuvora.db). Verificado que:

· NO es de Telegram (comprobado en commit cae7bcb sin código de 14.11: 30 fallos)
· NO afecta a producción
· NO afecta a tests individuales (todos pasan aislados)

Anotado como Deuda 11 en el documento maestro.
Fase propuesta: 14.15 (Test Suite Isolation).

Mejora parcial en 14.11.18: test_models_14_3.py tenía 2 errores por fixture source_id inexistente → arreglado.

---

🚫 No incluido en 14.11 (futuro)

· ❌ WhatsApp, Discord, Instagram, Messenger, SMS
· ❌ Grupos de Telegram
· ❌ Canales de Telegram
· ❌ Comandos avanzados
· ❌ Media (fotos, audio, vídeo)
· ❌ Inline keyboards
· ❌ Telegram Mini Apps
· ❌ SDK oficial de Telegram
· ❌ Marketplace
· ❌ Redis (queda para 14.13)
· ❌ Billing por mensaje

14.11 se centra en: demostrar que Nuvora es multicanal con Telegram como primer canal externo real.

---

🎯 Resultado final

Al terminar 14.11, Nuvora puede decir:

"Crea tu bot en Nuvora y conéctalo a Web, API o Telegram — el mismo Core, los mismos workflows, cero duplicación."

```
MI TELEGRAM
   │
   │ "Hola"
   ▼
TELEGRAM API
   │
   ▼
NUVORA WEBHOOK
   │
   ▼
NUVORA CORE
   │
   ▼
WORKFLOW ENGINE
   │
   ▼
RESPUESTA
   │
   ▼
MI TELEGRAM
```

---

Próximo: 14.12 — Creator Mode

(Pendiente de diseño por el owner)

---

Fin del CHANGELOG 14.11
