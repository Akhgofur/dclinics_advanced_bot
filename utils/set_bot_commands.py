from aiogram import Bot, types


async def set_default_commands(bot: Bot):
    await bot.set_my_commands(
        [
            types.BotCommand(command="start", description="Запустить бота"),
            types.BotCommand(command="reset", description="Начать заново"),
            types.BotCommand(command="help", description="Помощь"),
            # types.BotCommand(command="change_language", description="Tilni o‘zgartirish"),
        ]
    )
