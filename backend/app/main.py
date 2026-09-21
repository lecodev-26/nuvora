import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routers import (
    bots, memories, ask, auth, payments, analytics, categories, sources, training,
    workflows,
    ai_config,
    ai_workflows,
    tests,
    publication,
    public,
    api_keys,
    api_v1,
    telegram,
    telegram_webhook,
)

load_dotenv()

# ============================================================
# OPENAPI TAGS (14.10.9)
# ============================================================
OPENAPI_TAGS = [
    {
        "name": "api-v1",
        "description": (
            "**Nuvora API v1** — Endpoints públicos para integraciones externas.\n\n"
            "Autenticación: `Authorization: Bearer nvr_live_...`\n\n"
            "**Ejemplo:**\n"
            "```\n"
            "curl https://nuvora-api-1hql.onrender.com/api/v1/chat \\\n"
            "  -H \"Authorization: Bearer nvr_live_...\" \\\n"
            "  -H \"Content-Type: application/json\" \\\n"
            "  -d '{\"message\": \"Hola\"}'\n"
            "```"
        ),
        "externalDocs": {
            "description": "Documentación completa",
            "url": "https://nuvora-chi.vercel.app",
        },
    },
    {
        "name": "api-keys",
        "description": (
            "**Gestión de API Keys** del panel privado (JWT).\n\n"
            "Permite crear, listar y revocar API keys por bot.\n\n"
            "El secret completo solo se muestra **una vez** al crear la key."
        ),
    },
    {
        "name": "public",
        "description": (
            "**Bot público** — Endpoints sin JWT para la página `/b/:slug` y el widget.\n\n"
            "Sin autenticación. Rate limiting por IP."
        ),
    },
    {
        "name": "bots",
        "description": "CRUD de bots (panel privado, JWT).",
    },
    {
        "name": "workflows",
        "description": "CRUD de workflows + ejecución (panel privado, JWT).",
    },
    {
        "name": "tests",
        "description": "Bot Tester — generar, testear, analizar workflows.",
    },
    {
        "name": "auth",
        "description": "Registro, login y gestión de sesión JWT.",
    },
]


app = FastAPI(
    title=os.getenv("APP_NAME", "Nuvora API"),
    description=(
        "Chatbot universal para negocios.\n\n"
        "Incluye: **Nuvora API v1** para integraciones externas "
        "(`/api/v1/*`), gestión de API Keys, bots, workflows y Bot Tester."
    ),
    version=os.getenv("APP_VERSION", "0.1.0"),
    openapi_tags=OPENAPI_TAGS,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://nuvora-chi.vercel.app",
        "http://localhost:5173",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# CORS PÚBLICO (Fase 14.9.8)
# ============================================================
# Endpoints /public/* son consumidos desde dominios de terceros
# (widget embebido en webs de clientes). Aplicamos un CORS abierto
# SOLO a esas rutas, sin cookies ni credenciales.
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware as StarletteCORS


class PublicCORSMiddleware(BaseHTTPMiddleware):
    """
    Aplica CORS abierto SOLO a rutas /public/*.
    Las demás rutas usan el CORS estricto definido arriba.
    """

    async def dispatch(self, request, call_next):
        # CORS abierto para endpoints públicos y webhooks externos
        if request.url.path.startswith("/public/") or request.url.path.startswith("/webhooks/"):
            # Simula los headers CORS para permitir cualquier origen
            if request.method == "OPTIONS":
                from starlette.responses import Response
                headers = {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Max-Age": "600",
                }
                return Response(status_code=204, headers=headers)

            response = await call_next(request)
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            return response

        return await call_next(request)


app.add_middleware(PublicCORSMiddleware)

app.include_router(bots.router)
app.include_router(memories.router)
app.include_router(ask.router)
app.include_router(auth.router)
app.include_router(payments.router)
app.include_router(analytics.router)
app.include_router(categories.router)
app.include_router(sources.router)
app.include_router(training.router)
app.include_router(workflows.router)  # ← NUEVO 14.5.7
app.include_router(ai_config.router)  # ← NUEVO 14.7.4b (BYOK)
app.include_router(ai_workflows.router)  # ← NUEVO 14.7.7 (AI Workflow Designer)
app.include_router(tests.router)  # ← NUEVO 14.8.7 (Bot Tester)
app.include_router(publication.router)  # ← NUEVO 14.9.5 (Publicación Universal)
app.include_router(public.router)  # ← NUEVO 14.9.8 (Endpoints públicos)
app.include_router(api_keys.router)  # ← NUEVO 14.10.6 (Nuvora API - gestión de keys)
app.include_router(api_v1.router)  # ← NUEVO 14.10.7 (Nuvora API - chat)
app.include_router(telegram.router)  # ← NUEVO 14.11.8 (Telegram - gestión privada)
app.include_router(telegram_webhook.router)  # ← NUEVO 14.11.9 (Telegram - webhook público)

# ============================================================
# API v1 — Errores uniformes (14.10.8)
# ============================================================
from app.core.api_errors import register_api_error_handlers
register_api_error_handlers(app)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": os.getenv("APP_NAME", "nuvora-api"),
        "version": os.getenv("APP_VERSION", "0.1.0")
    }

@app.get("/")
def root():
    return {
        "message": "Welcome to Nuvora API",
        "docs": "/docs"
    }
