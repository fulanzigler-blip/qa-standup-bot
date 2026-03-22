import asyncio
import logging
import os

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from telegram.ext import Application

from app.bot.router import setup_router

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def main() -> None:
    bot_token = os.getenv("BOT_TOKEN")
    database_url = os.getenv("DATABASE_URL")

    if not bot_token:
        raise ValueError("BOT_TOKEN environment variable is required")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")

    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    application = Application.builder().token(bot_token).build()
    setup_router(application, session_factory)

    logger.info("Starting bot...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)

    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()
        await engine.dispose()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
