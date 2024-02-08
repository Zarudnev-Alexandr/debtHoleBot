import asyncio

from aiogram import Bot, Dispatcher
from aiogram.utils.callback_answer import CallbackAnswerMiddleware
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from bot.config_reader import config
from bot.handlers import commands, callbacks, state
from bot.middlewares import DbSessionMiddleware
# from bot.ui_commands import set_ui_commands


async def main():
    engine = create_async_engine(url=str(config.db_url), echo=True)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    bot = Bot(config.bot_token.get_secret_value(), parse_mode="HTML")

    dp = Dispatcher()
    dp.update.middleware(DbSessionMiddleware(session_pool=sessionmaker))
    dp.callback_query.middleware(CallbackAnswerMiddleware())

    dp.include_router(commands.router)
    dp.include_router(callbacks.router)
    dp.include_router(state.router)

    # await set_ui_commands(bot)

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())
