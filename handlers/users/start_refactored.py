"""Main message handler - refactored version."""
import re
from datetime import datetime
from aiogram import Router, F, Command
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from utils.helpers import get_translation
from utils.constants import StateStep, DateTimeFormats
from utils.state_helpers import get_state_data
from utils.message_helpers import get_language
from keyboards.inline.main import get_gender_keyboard, get_confirm_keyboard, get_today_keyboard
from keyboards.default.main import get_add_service_keyboard
from handlers.users.patient_handlers import (
    handle_patient,
    handle_language_request,
    handle_contact
)
from handlers.users.service_handlers import handle_fetch_services, handle_fetch_doctor_services
from handlers.users.pdf_handlers import handle_code

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command."""
    lang = await get_language(state)
    
    # Handle /start with code parameter
    if message.text and len(message.text.split(" ")) == 2:
        code = message.text.split(" ")[1]
        await handle_code(message, state, customCode=code)
        return
    
    await message.answer(
        get_translation(lang, 'welcome'),
        reply_markup=ReplyKeyboardRemove(),
    )
    await handle_patient(message, state)


@router.message(Command("reset"))
async def cmd_reset(message: Message, state: FSMContext):
    """Handle /reset command."""
    lang = await get_language(state)
    
    await message.answer(
        get_translation(lang, 'reset'),
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.clear()
    await handle_language_request(message, state)


@router.message(F.contact)
async def handle_contact_message(message: Message, state: FSMContext):
    """Handle contact message."""
    state_data = await get_state_data(state)
    if state_data.step == StateStep.PHONE:
        await handle_contact(message, state, False)


@router.message(F.text)
async def handle_text_messages(message: Message, state: FSMContext):
    """Handle text messages based on state and content."""
    state_data = await get_state_data(state)
    lang = state_data.language
    step = state_data.step
    add_patient = state_data.add_patient
    phone_number = state_data.phone_number
    
    # Get translated button texts
    services_text = get_translation(lang, "services")
    add_service_text = get_translation(lang, "add_service")
    change_lang_text = get_translation(lang, "change_lang")
    
    # Patient registration flow
    if add_patient and phone_number and step != StateStep.BIRTHDAY:
        await _handle_patient_name_input(message, state)
        return
    
    # Birthday input
    if step == StateStep.BIRTHDAY:
        await _handle_birthday_input(message, state)
        return
    
    # Registration date input
    if step == StateStep.REGISTRATION_DATE:
        await _handle_registration_date_input(message, state)
        return
    
    # Main menu commands
    if message.text == services_text:
        await handle_fetch_services(message, state)
        return
    
    if message.text == add_service_text:
        add_service_kb = await get_add_service_keyboard(state)
        await message.answer(
            get_translation(lang, "add_serv"),
            reply_markup=add_service_kb
        )
        return
    
    if message.text == change_lang_text:
        await handle_language_request(message, state)
        return
    
    # Numeric code for PDF
    if re.match(r"^\d+$", message.text):
        await handle_code(message, state, message.text)
        return


async def _handle_patient_name_input(message: Message, state: FSMContext):
    """Handle patient name input during registration."""
    state_data = await get_state_data(state)
    lang = state_data.language
    phone_number = state_data.phone_number
    
    message_text = message.text.split(" ")
    
    if len(message_text) < 2:
        await message.answer(
            f"{get_translation(lang, 'write_name_for_registration')}\n"
            f"{get_translation(lang, 'name_example')}",
            reply_markup=ReplyKeyboardRemove(),
        )
        return
    
    first_name = message_text[0]
    last_name = message_text[1]
    
    patient_form = state_data.patient_form or {"phone": phone_number}
    patient_form["first_name"] = first_name
    patient_form["last_name"] = last_name
    
    await state.update_data(patient_form=patient_form)
    await message.answer(
        get_translation(lang, 'select_gender'),
        reply_markup=await get_gender_keyboard(state),
    )


async def _handle_birthday_input(message: Message, state: FSMContext):
    """Handle birthday input."""
    state_data = await get_state_data(state)
    lang = state_data.language
    patient_form = state_data.patient_form
    
    try:
        day, month, year = message.text.split(".")
        
        if not (day.isdigit() and month.isdigit() and year.isdigit()):
            await message.answer(get_translation(lang, 'select_birthday'))
            return
        
        selected_date = "-".join([year, month, day])
        patient_form['birthday'] = selected_date
        
        await state.update_data(patient_form=patient_form, step=StateStep.CHECK_DATA)
        
        gender = patient_form.get('gender', '')
        gender_text = 'male' if gender == 1 else 'female'
        
        message_text = (
            f"<b>{get_translation(lang, 'is_correct')}:</b>\n"
            f"{get_translation(lang, 'name')}: {patient_form.get('first_name', '')} "
            f"{patient_form.get('last_name', '')}\n"
            f"{get_translation(lang, 'phone')}: {patient_form.get('phone', '')}\n"
            f"{get_translation(lang, 'birthday')}: {selected_date}\n"
            f"{get_translation(lang, 'gender')}: {get_translation(lang, gender_text)}"
        )
        
        confirm_kb = await get_confirm_keyboard(state)
        await message.answer(message_text, reply_markup=confirm_kb)
        
    except Exception:
        await message.answer(get_translation(lang, "select_birthday"))


async def _handle_registration_date_input(message: Message, state: FSMContext):
    """Handle registration date input."""
    state_data = await get_state_data(state)
    lang = state_data.language
    service = state_data.service
    
    try:
        day, month, year = message.text.split(".")
        
        if not (day.isdigit() and month.isdigit() and year.isdigit()):
            today_kb = await get_today_keyboard(state)
            await message.answer(
                get_translation(lang, 'select_admission_date'),
                reply_markup=today_kb
            )
            return
        
        selected_date = "-".join([year, month, day])
        service['registration_date'] = selected_date
        
        await state.update_data(service=service, step="")
        message_text = get_translation(lang, "select_admission_time")
        await handle_fetch_doctor_services(message, state, message_text)
        
    except Exception as e:
        print(f"Error in registration date input: {e}")
        today_kb = await get_today_keyboard(state)
        await message.answer(
            get_translation(lang, "select_admission_date"),
            reply_markup=today_kb
        )
