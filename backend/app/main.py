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
)

load_dotenv()

app = FastAPI(
    title=os.getenv("APP_NAME", "Nuvora API"),
    description="Chatbot universal para negocios",
    version=os.getenv("APP_VERSION", "0.1.0")
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
        if request.url.path.startswith("/public/"):
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
