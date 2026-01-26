from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    FSInputFile,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ContentType,
    ReplyKeyboardRemove,
)


from aiogram.fsm.context import FSMContext

from utils.helpers import get_translation

async def get_request_contact_keyboard(state: FSMContext) -> InlineKeyboardMarkup:
    data = await state.get_data()
    lang = data.get("language", "ru")

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=f"📱 {get_translation(lang, 'send_number')}",
                    request_contact=True,
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )





async def get_main_keyboard(state: FSMContext) -> ReplyKeyboardMarkup:
    """Get main menu keyboard."""
    data = await state.get_data()
    lang = data.get("language", "ru")

    services = get_translation(lang, "services")
    add_service = get_translation(lang, "add_service")
    change_lang = get_translation(lang, "change_lang")

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=services),
                KeyboardButton(text=add_service),
            ],
            [
                KeyboardButton(text=change_lang)
            ],
        ],
        resize_keyboard=True,
    )


async def get_services_print_keyboard(state: FSMContext) -> ReplyKeyboardMarkup:
    data = await state.get_data()
    lang = data.get("language", "ru")

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=f"{get_translation(lang, 'print_results')}",
                ),
                KeyboardButton(
                    text=f"{get_translation(lang, 'come_back')}",
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
