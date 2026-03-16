import asyncio
import os

from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID_RAW = os.environ.get("TELEGRAM_ADMIN_CHAT_ID")


async def main():
    if not TOKEN or not CHAT_ID_RAW:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN and TELEGRAM_ADMIN_CHAT_ID before running")

    bot = Bot(token=TOKEN)
    await bot.send_message(
        chat_id=int(CHAT_ID_RAW),
        text="Привет! Это тестовое сообщение от бота.",
    )
    print("Сообщение отправлено.")


if __name__ == "__main__":
    asyncio.run(main())
