"""Handlers for cart-related operations."""
from datetime import datetime
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from utils.api_client import api_client
from utils.helpers import get_translation, get_safe_attribute
from utils.constants import DateTimeFormats
from utils.state_helpers import get_state_data
from utils.message_helpers import loading_message, send_error_message, get_language
from utils.keyboard_helpers import get_main_keyboard
from keyboards.inline.main import get_cart_keyboard
from services.text_builder import TextBuilder


async def handle_open_cart(
    callback: CallbackQuery,
    state: FSMContext,
    additional_text: str = ""
):
    """Display cart contents."""
    state_data = await get_state_data(state)
    lang = state_data.language
    cart_services = state_data.cart

    cart_text = TextBuilder.build_cart_text(cart_services, lang)
    message = f"{additional_text}<b>{get_translation(lang, 'cart_services')}</b>\n\n{cart_text}"

    await callback.message.answer(
        message,
        reply_markup=await get_cart_keyboard(state)
    )


async def handle_post_admittance(message: Message, state: FSMContext):
    """Create admittance from cart."""
    state_data = await get_state_data(state)
    cart = state_data.cart
    
    if not cart:
        # Note: handle_open_cart expects CallbackQuery, but we have Message
        # This needs to be handled differently
        lang = await get_language(state)
        cart_text = TextBuilder.build_cart_text([], lang)
        from keyboards.inline.main import get_cart_keyboard
        await message.answer(
            f"<b>{get_translation(lang, 'cart_services')}</b>\n\n{cart_text}",
            reply_markup=await get_cart_keyboard(state)
        )
        return
    
    async with loading_message(message, state) as _:
        try:
            services = [
                {
                    "doctor": get_safe_attribute(item, "doctor"),
                    "admittanceType": get_safe_attribute(item, "admittanceType"),
                    "registrationDate": get_safe_attribute(item, "registrationDate"),
                    'quantity': 1,
                    'patient': state_data.patient_id,
                    'amount': float(get_safe_attribute(item, 'admittanceType_obj.amount', 0)),
                    'totalAmount': float(get_safe_attribute(item, 'admittanceType_obj.amount', 0)),
                    'paidAmount': float(get_safe_attribute(item, 'admittanceType_obj.amount', 0)),
                    'isCome': False,
                    'preBooking': True
                }
                for item in cart
            ]
            
            admittance = {
                "patient": state_data.patient_id,
                "registrationDate": datetime.now().strftime(DateTimeFormats.ISO_DATETIME),
                "services": services,
                'source': 2
            }
            
            data = await api_client.create_admittance(admittance)
            
            if not data:
                raise Exception("Failed to create admittance")
            
            await state.update_data(cart=[], service={})
            lang = await get_language(state)
            await message.answer(
                get_translation(lang, 'service_saved'),
                reply_markup=await get_main_keyboard(state),
            )
                
        except Exception:
            await send_error_message(message, state, 'error_try')
