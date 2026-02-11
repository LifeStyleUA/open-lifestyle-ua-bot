import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from app.core.config import settings
from app.handlers.start import router
from app.db.session import init_db
from app.middlewares.error_handler import ErrorMiddleware


async def main():
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    # Initialize DB (create explained tables)
    await init_db()

    bot = Bot(
        token=settings.BOT_TOKEN,
        parse_mode=ParseMode.HTML,
    )

    dp = Dispatcher()

    # Register global error middleware
    dp.update.middleware(ErrorMiddleware())

    # Include routers
    dp.include_router(router)

    logging.info("Bot started in polling mode")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
