from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.leadvault import router as leadvault_router
from config import settings


app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(leadvault_router)


@app.get("/")
def root():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "docs": "/docs",
        "health": "/api/leadvault/health",
    }
