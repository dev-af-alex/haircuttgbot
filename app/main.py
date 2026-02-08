import json
import logging
import os

from aiogram import Dispatcher
from fastapi import FastAPI

LOGGER = logging.getLogger("bot_api")
logging.basicConfig(level=logging.INFO, format="%(message)s")

app = FastAPI(title="haircuttgbot-api", version="0.1.0")


@app.on_event("startup")
def on_startup() -> None:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")

    # Keep aiogram integration point present in runtime skeleton.
    _dispatcher = Dispatcher()
    _ = _dispatcher

    LOGGER.info(
        json.dumps(
            {
                "event": "startup",
                "service": "bot-api",
                "telegram_token_configured": bool(bot_token),
            }
        )
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "bot-api"}
