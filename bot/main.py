"""Entry point for the Mira Telegram bot."""

from __future__ import annotations

import os
from dotenv import load_dotenv

from telegram.ext import ApplicationBuilder

from backend.database import create_tables
from data.tasks import seed_tasks
from bot.handlers import get_conversation_handler


def main() -> None:
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set in .env")

    create_tables()
    seed_tasks()

    app = ApplicationBuilder().token(token).build()
    app.add_handler(get_conversation_handler())

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
