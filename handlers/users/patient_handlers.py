"""Handlers for patient-related operations."""
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from utils.api_client import api_client
from utils.helpers import get_translation, get_full_name, get_safe_attribute
from utils.constants import CallbackData, StateStep
from utils.state_helpers import get_state_data
from utils.message_helpers import loading_message, get_language
from utils.keyboard_helpers import get_main_keyboard
from keyboards.inline.main import get_confirm_keyboard, get_gender_keyboard, get_language_kb
from keyboards.default.main import get_request_contact_keyboard


async def handle_language_request(message: Message, state: FSMContext):
    """Handle language selection request."""
    lang = await get_language(state)
    await message.answer(
        get_translation(lang, 'select_lang'),
        reply_markup=get_language_kb()
    )


async def handle_patient(message: Message, state: FSMContext):
    """Handle patient authentication flow."""
    state_data = await get_state_data(state)
    lang = state_data.language
    patient_id = state_data.patient_id

    if lang is None:
        await handle_language_request(message, state)
    elif patient_id:
        await message.answer(
            get_translation(lang, 'select_action'),
            reply_markup=await get_main_keyboard(state)
        )
    else:
        await state.update_data(step=StateStep.PHONE)
        request_contact_keyboard = await get_request_contact_keyboard(state)
        await message.answer(
            get_translation(lang, 'request_number'),
            reply_markup=request_contact_keyboard,
        )


async def handle_contact(message: Message, state: FSMContext, from_message: bool = False):
    """Handle contact/phone number input."""
    phone_number = message.text if from_message else message.contact.phone_number
    await state.update_data(phone_number=phone_number, step="")

    lang = await get_language(state)
    await message.answer(
        f"{get_translation(lang, 'number_received')} {phone_number}",
        reply_markup=ReplyKeyboardRemove(),
    )
    
    async with loading_message(message, state, "patient_finding") as _:
        patient = await api_client.get_patient_by_phone(phone_number)

    if patient:
        await state.update_data(
            patient_id=patient["id"],
            patient_guid=patient["guid"],
            patient_first_name=patient["first_name"],
            patient_last_name=patient["last_name"],
        )
        confirm_kb = await get_confirm_keyboard(state)
        await message.answer(
            f"{get_translation(lang, 'name')}: {get_full_name(patient)}\n"
            f"{get_translation(lang, 'birthday')}: {get_safe_attribute(patient, 'birthday')}\n\n"
            f"{get_translation(lang, 'is_your_data')}",
            reply_markup=confirm_kb,
        )
    else:
        await state.update_data(
            add_patient=True,
            patient_form={"phone": phone_number}
        )
        await message.answer(
            f"{get_translation(lang, 'record_not_found')}\n"
            f"{get_translation(lang, 'write_name_for_registration')}\n"
            f"{get_translation(lang, 'name_example')}",
        )


async def process_confirmation(callback: CallbackQuery, state: FSMContext):
    """Process patient data confirmation."""
    state_data = await get_state_data(state)
    phone = state_data.phone_number
    lang = state_data.language

    if callback.data == CallbackData.CONFIRM_YES:
        await callback.message.answer(
            f"✅ {get_translation(lang, 'confirmed')}: {phone}",
            reply_markup=await get_main_keyboard(state)
        )
    else:
        await state.update_data(
            patient_guid=None,
            patient_id=None,
            patient_first_name=None,
            patient_last_name=None,
            add_patient=True,
            patient_form={"phone": phone}
        )
        await callback.answer()
        await callback.message.answer(
            f"{get_translation(lang, 'write_name_for_registration')}\n"
            f"{get_translation(lang, 'name_example')}",
        )


async def handle_post_patient(message: Message, state: FSMContext):
    """Handle patient creation."""
    state_data = await get_state_data(state)
    lang = state_data.language
    
    async with loading_message(message, state) as _:
        try:
            patient_data = state_data.patient_form
            data = await api_client.create_patient(patient_data)
            
            if not data:
                raise Exception("Failed to create patient")
            
            await state.update_data(
                patient_id=data["id"],
                patient_guid=data["guid"],
                patient_first_name=data["first_name"],
                patient_last_name=data["last_name"],
                add_patient=False,
                step="",
            )
            patient_name = f"{data['first_name']} {data['last_name']}"
            await message.answer(
                f"✅ {get_translation(lang, 'confirmed')}: {patient_name}",
                reply_markup=await get_main_keyboard(state)
            )
                
        except Exception:
            from utils.message_helpers import send_error_message
            await send_error_message(message, state)
            await state.update_data(add_patient=True, step="")
            await message.answer(
                f"{get_translation(lang, 'write_name_for_registration')}\n"
                f"{get_translation(lang, 'name_example')}",
            )


async def process_patient_add_confirmation(callback: CallbackQuery, state: FSMContext):
    """Process patient addition confirmation."""
    if callback.data == CallbackData.CONFIRM_YES:
        await handle_post_patient(callback.message, state)
    else:
        lang = await get_language(state)
        await state.update_data(add_patient=True, step="")
        await callback.message.answer(
            f"{get_translation(lang, 'write_name_for_registration')}\n"
            f"{get_translation(lang, 'name_example')}",
        )
        await callback.message.edit_reply_markup()
        await callback.answer()


async def handle_language(callback: CallbackQuery, state: FSMContext):
    """Handle language selection."""
    await state.update_data(language=callback.data)
    await callback.answer()
    await handle_patient(callback.message, state)


# Message handlers moved to start_refactored to avoid conflicts
