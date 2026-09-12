import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routers import (
    bots, memories, ask, auth, payments, analytics, categories, sources, training,
    workflows,
    ai_config,
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
