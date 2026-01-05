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


async def get_confirm_keyboard(state: FSMContext) -> InlineKeyboardMarkup:
    data = await state.get_data()
    lang = data.get("language", "ru")

    yes_text = get_translation(lang, "yes")
    no_text = get_translation(lang, "no")

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"✅ {yes_text}", callback_data="confirm_yes"
                ),
                InlineKeyboardButton(text=f"❌ {no_text}", callback_data="confirm_no"),
            ]
        ]
    )


async def get_gender_keyboard(state: FSMContext) -> InlineKeyboardMarkup:
    data = await state.get_data()
    lang = data.get("language", "ru")

    male = get_translation(lang, "male")
    female = get_translation(lang, "female")

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"{male}", callback_data="male"),
                InlineKeyboardButton(text=f"{female}", callback_data="female"),
            ]
        ]
    )


async def get_today_keyboard(state: FSMContext) -> InlineKeyboardMarkup:
    data = await state.get_data()
    lang = data.get("language", "ru")

    today = get_translation(lang, "today")

    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=f"{today}", callback_data="today")]]
    )


async def get_cart_keyboard(state: FSMContext) -> InlineKeyboardMarkup:
    data = await state.get_data()
    lang = data.get("language", "ru")
    cart_services = data.get("cart", [])

    save_admittance = get_translation(lang, "save_admittance")
    add_serv = get_translation(lang, "add_serv")
    delete_serv = get_translation(lang, "delete_service")
    clear_cart = get_translation(lang, "clear_cart")

    if not cart_services:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"➕{add_serv}", callback_data="add_service"
                    ),
                ],
            ]
        )
    
    
    
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"✅{save_admittance}", callback_data="save_admittance"
                ),
                InlineKeyboardButton(text=f"➕{add_serv}", callback_data="add_service"),
            ],
            [
                # InlineKeyboardButton(
                #     text=f"{delete_serv}", callback_data="delete_service"
                # ),
                InlineKeyboardButton(text=f"🧹{clear_cart}", callback_data="clear_cart"),
            ],
        ]
    )


async def get_add_service_keyboard(state: FSMContext) -> InlineKeyboardMarkup:
    data = await state.get_data()
    lang = data.get("language", "ru")

    add_serv = get_translation(lang, "add_serv")
    cart = get_translation(lang, "cart")

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"🛒{cart}", callback_data="cart"),
                InlineKeyboardButton(text=f"➕{add_serv}", callback_data="add_service"),
            ]
        ]
    )


async def get_come_back_keyboard(
    state: FSMContext, call_data="come_back"
) -> InlineKeyboardMarkup:
    data = await state.get_data()
    lang = data.get("language", "ru")

    come_back = get_translation(lang, "come_back")

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{come_back}", callback_data=call_data)]
        ]
    )


# Keyboards
def get_language_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="O'zbek", callback_data="uz")],
            [InlineKeyboardButton(text="Русский", callback_data="ru")],
            [InlineKeyboardButton(text="English", callback_data="en")],
        ]
    )
