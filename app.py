import asyncio
from aiogram import Dispatcher
from loader import dp, bot
from handlers.users import start  # your handlers file
from utils.notify_admins import on_startup_notify
from utils.set_bot_commands import set_default_commands
from environs import Env

# Optional: load environment variables (if not done in loader.py)
env = Env()
env.read_env()

async def on_startup():
    await set_default_commands(bot)
    await on_startup_notify(bot)

async def main():
    # ✅ Register routers here
    dp.include_router(start.router)

    # ✅ Run startup routines
    await on_startup()

    # ✅ Start polling
    print("Bot started.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
