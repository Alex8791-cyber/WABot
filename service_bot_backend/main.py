# service_bot_backend/main.py
"""AI Service Bot Backend — FastAPI application entrypoint."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import ALLOWED_ORIGINS, DATABASE_FILE
from database import init_db
from routes import agent, services, features, health, webhook

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("service_bot")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(DATABASE_FILE)
    logger.info("Service Bot Backend starting")
    yield
    logger.info("Shutting down")


app = FastAPI(title="AI Service Bot API", version="3.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(agent.router)
app.include_router(services.router)
app.include_router(features.router)
app.include_router(health.router)
app.include_router(webhook.router)
