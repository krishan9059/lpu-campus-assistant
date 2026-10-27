from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import admin, assistants, auth, chat, health, placement

api_router = APIRouter()
for module in (health, assistants, auth, chat, placement, admin):
    api_router.include_router(module.router)
