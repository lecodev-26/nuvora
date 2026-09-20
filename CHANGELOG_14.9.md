# CHANGELOG 14.9 — Publicación Universal

**Fecha de cierre:** 20 de septiembre de 2026
**Estado:** ✅ COMPLETADA
**Tests:** 358 (180 backend + 178 frontend)

---

## 🎯 Objetivo

Convertir un bot de Nuvora en algo **publicable y consumible externamente**, sin que el visitante entre al panel.

**Ciclo cerrado:** `crear bot → entrenar → diseñar workflow → IA → testear → PUBLICAR`

---

## 📋 Subfases (14.9.1 → 14.9.15)

| # | Subfase | Estado |
|---|---|---|
| 14.9.1 | Auditoría + diseño | ✅ |
| 14.9.2 | Modelo `Bot.public_*` + tabla `public_sessions` + migración | ✅ |
| 14.9.3 | Schemas Pydantic (public.py) | ✅ |
| 14.9.4 | Generador de `public_id` (UUID) + `public_slug` | ✅ |
| 14.9.5 | Endpoints privados (publish / unpublish / publication) | ✅ |
| 14.9.6 | Public resolver (único punto de acceso) | ✅ |
| 14.9.7 | Public session service (sesiones anónimas 1h) | ✅ |
| 14.9.8 | Endpoints públicos E2E (con WorkflowEngine) | ✅ |
| 14.9.9 | Rate limiting público (IP + session) | ✅ |
| 14.9.10 | Página pública (`/b/:identifier`) | ✅ |
| 14.9.11 | Integración Builder (botón 🚀 Publicar) | ✅ |
| 14.9.12 | Widget refactor (dual: legacy + público) | ✅ |
| 14.9.13 | Seguridad + abuse protection | ✅ |
| 14.9.14 | E2E global (flujo completo) | ✅ |
| 14.9.15 | Deploy + verificación prod + cierre | ✅ |

---

## 🔑 Principios aplicados

1. `public_id` = UUID v4 (identidad técnica)
2. `public_slug` = URL humana opcional
3. `public_config` = solo visual/textos (nunca workflow, provider, prompt)
4. Sesión blindada: `public_id → session_id → bot_id` verificados
5. `public_sessions` = contexto mínimo (no analytics)
6. Widget = refactor quirúrgico (no reescritura)
7. **WorkflowEngine 14.5 = único motor** (cero duplicación)
8. E2E real en producción obligatorio

---

## 🏗️ Arquitectura final

```

Panel privado  ──┐
Bot Tester     ──┼──►  WorkflowEngine 14.5  ──►  respuesta
Bot público    ──┘

```

**Una sola puerta al motor. Cero duplicación.**

---

## 📦 Endpoints añadidos

**Privados (JWT):**
- `GET    /bots/{bot_id}/publication`
- `PUT    /bots/{bot_id}/publication`
- `POST   /bots/{bot_id}/publish`
- `POST   /bots/{bot_id}/unpublish`

**Públicos (sin JWT):**
- `GET    /public/bots/{identifier}`
- `POST   /public/bots/{identifier}/session`
- `POST   /public/bots/{identifier}/message`
- `DELETE /public/bots/{identifier}/session`

---

## 🗄️ Cambios en BD

**Extendida `bots`:** `public_id`, `public_slug`, `published_at`, `public_config`

**Nueva `public_sessions`:** `id`, `public_id`, `bot_id`, `session_data`, `status`, `expires_at`

**Migración:** `backend/migrations/migrate_prod_14_9.py` (idempotente)

---

## 🎨 Frontend

**Ficheros nuevos:**
- `src/services/publicApi.js`
- `src/services/publicationApi.js`
- `src/components/public/PublicHeader.jsx`
- `src/components/public/PublicFooter.jsx`
- `src/components/public/PublicChat.jsx`
- `src/components/publication/PublicationPanel.jsx`
- `src/pages/PublicBot.jsx`

**Ficheros modificados:**
- `src/App.jsx` (+ ruta `/b/:identifier`)
- `src/pages/WorkflowBuilder.jsx` (+ botón 🚀 Publicar)
- `src/pages/Dashboard.jsx` (+ snippet `data-bot-public-id`)

**Fix SPA:** `frontend/vercel.json` (rewrite SPA)

---

## 🧩 Widget

**`widget/widget.js` (611 líneas):**
- Dual mode: `data-bot-public-id` (nuevo) o `data-bot-id` (legacy)
- Modo público: `/public/bots/{id}` + `/session` + `/message`
- Modo legacy: `/bots/{id}/public` + `/ask/public`
- Config visual del servidor (welcome, placeholder, color, avatar, branding)

---

## 🛡️ Seguridad

- **Enumeración:** 20 public_ids + 20 session_ids random → todos 404
- **Payloads:** límites 2000 chars + validación Pydantic
- **Cross-bot:** session del bot A no sirve en bot B → 404
- **No filtrado:** endpoint público NO expone 11 campos internos
- **SQL injection / XSS:** tratados como texto
- **Rate limiting:** por IP + por session_id → 429 con `Retry-After`
- **CORS:** abierto solo para `/public/*`, sin cookies
- **Bot no publicado:** accesos públicos → 404

---

## 🚀 Migración PostgreSQL (18-20 sep 2026)

**Motivo:** Render PostgreSQL Free se suspende el 9 octubre 2026.

**Acciones:**
- Backup FULL (56 KB) + SCHEMA (45 KB) de Render
- Aiven PostgreSQL Free creado (Amsterdam, PG 18.6)
- Estructura restaurada (12 tablas + índices + FKs)
- `DATABASE_URL` en Render → Aiven
- Verificación E2E completa en prod
- Aiven limpiado (0 filas)

**URLs producción:**
- Backend: `https://nuvora-api-1hql.onrender.com` → Aiven
- Frontend: `https://nuvora-chi.vercel.app`
- Render PG: intacta (fallback temporal)

---

## 📊 Tests

| Suite | Tests |
|---|---|
| Backend 14.9 nuevos | 180 |
| Frontend 14.9 nuevos | 71 |
| Frontend heredados | 107 |
| **TOTAL 14.9** | **358** |

**Regresión:** todo verde en cada subfase.

---

## 📌 Pendientes (fuera de 14.9)

- Vigilar logs 24-48h
- Borrar Render PostgreSQL (2-3 días)
- Dominio custom (futuro)
- Redis para rate limiting (14.13)
- Fix `datetime.utcnow()` deprecation (futuro)
- Tests E2E Playwright (futuro)

---

## 🎯 Estado final

- **14.9 completada al 100%**
- **Producción**: verificada end-to-end
- **Aiven**: funcionando, limpio
- **Widget**: refactorizado con dual mode
- **Página pública**: funcionando en `/b/:slug`
- **Cero duplicación de motores**

---

**Próximo:** 14.10 — API Nuvora
