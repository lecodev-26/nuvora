import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routers import bots, memories, ask

load_dotenv()

app = FastAPI(
    title=os.getenv("APP_NAME", "Nuvora API"),
    description="Chatbot para restaurantes",
    version=os.getenv("APP_VERSION", "0.1.0")
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bots.router)
app.include_router(memories.router)
app.include_router(ask.router)

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
