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





async def get_services_print_keyboard(state: FSMContext) -> InlineKeyboardMarkup:
    data = await state.get_data()
    lang = data.get("language", "ru")

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=f"{get_translation(lang, 'print_results')}",
                    request_contact=True,
                ),
                KeyboardButton(
                    text=f"{get_translation(lang, 'come_back')}",
                    request_contact=True,
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
