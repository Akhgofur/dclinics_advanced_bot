"""Handlers for callback queries."""
import re
from datetime import datetime
from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback

from utils.helpers import get_translation, get_full_name, get_safe_attribute
from utils.constants import (
    CallbackData, StateStep, DateTimeFormats
)
from utils.state_helpers import get_state_data
from utils.message_helpers import get_language
from keyboards.inline.main import (
    get_confirm_keyboard,
    get_add_service_keyboard,
    get_today_keyboard
)
from handlers.users.patient_handlers import (
    handle_language,
    process_confirmation,
    process_patient_add_confirmation,
    handle_language_request,
    handle_patient
)
from handlers.users.service_handlers import (
    handle_fetch_services,
    handle_fetch_doctors,
    handle_fetch_admittance_type,
    handle_fetch_doctor_services
)
from handlers.users.cart_handlers import handle_open_cart, handle_post_admittance
from handlers.users.pdf_handlers import handle_code

router = Router()


@router.callback_query()
async def handle_callback(callback: CallbackQuery, state: FSMContext):
    """Main callback query handler."""
    state_data = await get_state_data(state)
    add_patient = state_data.add_patient
    step = state_data.step
    callback_data = callback.data

    # Language selection
    if callback_data in [CallbackData.LANG_UZ, CallbackData.LANG_RU, CallbackData.LANG_EN]:
        await handle_language(callback, state)
        return

    # Patient confirmation
    if (callback_data in [CallbackData.CONFIRM_YES, CallbackData.CONFIRM_NO] 
            and not add_patient 
            and step != StateStep.SERVICE_CONFIRM):
        await callback.message.delete()
        await callback.answer()
        await process_confirmation(callback, state)
        return

    # Patient add confirmation
    if (callback_data in [CallbackData.CONFIRM_YES, CallbackData.CONFIRM_NO] 
            and add_patient 
            and step != StateStep.SERVICE_CONFIRM):
        await callback.message.delete()
        await callback.answer()
        await process_patient_add_confirmation(callback, state)
        return

    # Service confirmation
    if step == StateStep.SERVICE_CONFIRM:
        await callback.message.delete()
        await callback.answer()
        
        if callback_data == CallbackData.CONFIRM_YES:
            state_data = await get_state_data(state)
            cart = state_data.cart
            service = state_data.service
            cart.append(service)
            
            await state.update_data(service={}, step="", cart=cart)
            lang = state_data.language
            await callback.message.answer(get_translation(lang, "added_to_cart"))
            await handle_open_cart(callback, state)
        elif callback_data == CallbackData.CONFIRM_NO:
            await state.update_data(service={}, step="")
            lang = await get_language(state)
            await callback.message.answer(get_translation(lang, "canceled"))
            await handle_open_cart(callback, state)
        return

    # Navigation
    if callback_data == CallbackData.COME_BACK_ADD_SERVICE:
        await callback.message.delete()
        await callback.answer()
        state_data = await state.get_data()
        lang = state_data.get("language", Defaults.LANGUAGE)
        add_service_text = get_translation(lang, "add_serv")
        add_service_kb = await get_add_service_keyboard(state)
        await callback.message.answer(add_service_text, reply_markup=add_service_kb)
        return

    if callback_data == CallbackData.COME_BACK:
        await callback.message.delete()
        await callback.answer()
        await state.update_data(selected_services_print=[])
        await handle_patient(callback.message, state)
        return

    # Calendar handling
    if callback_data.startswith(CallbackData.SIMPLE_CALENDAR_PREFIX):
        await _handle_calendar_callback(callback, state)
        return

    # Service selection
    if callback_data.startswith(CallbackData.PRINT_SERVICE_PREFIX):
        await _handle_service_selection(callback, state)
        return

    # Doctor selection
    if callback_data.startswith(CallbackData.ADMITTANCE_DOCTOR_PREFIX):
        await _handle_doctor_selection(callback, state)
        return

    # Admittance type selection
    if callback_data.startswith(CallbackData.ADMITTANCE_TYPE_PREFIX):
        await _handle_admittance_type_selection(callback, state)
        return

    # Time selection
    if callback_data.startswith(CallbackData.SELECT_HOUR_PREFIX):
        await _handle_time_selection(callback, state)
        return

    # Gender selection
    if callback_data in [CallbackData.MALE, CallbackData.FEMALE]:
        await _handle_gender_selection(callback, state)
        return

    # Cart operations
    if callback_data == CallbackData.CART:
        await callback.message.delete()
        await callback.answer()
        await handle_open_cart(callback, state)
        return

    if callback_data == CallbackData.SAVE_ADMITTANCE:
        await callback.message.delete()
        await callback.answer()
        await handle_post_admittance(callback.message, state)
        return

    if callback_data == CallbackData.CLEAR_CART:
        await callback.message.delete()
        await callback.answer()
        await state.update_data(cart=[])
        lang = await get_language(state)
        cart_cleared_text = get_translation(lang, "cart_cleared")
        await handle_open_cart(callback, state, cart_cleared_text if cart_cleared_text else "")
        return

    # Service management
    if callback_data == CallbackData.ADD_SERVICE:
        await callback.message.delete()
        await callback.answer()
        await state.update_data(service={}, limit=Defaults.LIMIT, offset=Defaults.OFFSET, count=Defaults.COUNT)
        await handle_fetch_doctors(callback.message, state)
        return

    # Pagination
    if callback_data in [CallbackData.DOCTOR_PREV, CallbackData.DOCTOR_NEXT]:
        await _handle_doctor_pagination(callback, state)
        return

    if callback_data in [CallbackData.ADMITTANCE_TYPE_PREV, CallbackData.ADMITTANCE_TYPE_NEXT]:
        await _handle_admittance_type_pagination(callback, state)
        return

    # PDF/Results
    if callback_data == CallbackData.PRINT_RESULTS:
        await callback.message.delete()
        await callback.answer()
        await handle_code(callback.message, state, customCode=None, service=True)
        await state.update_data(selected_services_print=[])
        await handle_patient(callback.message, state)
        return

    # Numeric code
    if re.match(r"^\d+$", callback_data):
        await handle_code(callback.message, state, callback_data)
        return

    # Language change
    if callback_data == CallbackData.CHANGE_LANG:
        await callback.message.delete()
        await callback.answer()
        await handle_language_request(callback.message, state)
        return

    # Today button
    if step == StateStep.REGISTRATION_DATE and callback_data == CallbackData.TODAY:
        await callback.message.delete()
        await callback.answer()
        state_data = await state.get_data()
        lang = state_data.get("language", Defaults.LANGUAGE)
        service = state_data.get("service", {})
        
        selected_date = datetime.now().strftime(DateTimeFormats.ISO_DATE)
        service['registration_date'] = selected_date
        await state.update_data(service=service, step="")
        message_text = get_translation(lang, "select_admission_time")
        await handle_fetch_doctor_services(callback.message, state, message_text)
        return


async def _handle_calendar_callback(callback: CallbackQuery, state: FSMContext):
    """Handle calendar callback."""
    selected, date = await SimpleCalendar().process_selection(
        callback,
        SimpleCalendarCallback.unpack(callback.data)
    )
    
    if CallbackData.CANCEL in callback.data:
        await callback.message.delete()
        await callback.answer()
        await handle_fetch_doctors(callback.message, state)
        return
    
    if "TODAY" in callback.data:
        await callback.message.delete()
        await callback.answer()
        state_data = await state.get_data()
        lang = state_data.get("language", Defaults.LANGUAGE)
        service = state_data.get("service", {})
        
        selected_date = datetime.now().strftime(DateTimeFormats.ISO_DATE)
        service['registration_date'] = selected_date
        await state.update_data(service=service, step="")
        message_text = get_translation(lang, "select_admission_time")
        await handle_fetch_doctor_services(callback.message, state, message_text)
        return
    
    if selected:
        await callback.message.delete()
        await callback.answer()
        
        state_data = await state.get_data()
        lang = state_data.get("language", Defaults.LANGUAGE)
        service = state_data.get("service", {})
        
        # Validate date
        if date.date() < datetime.now().date() or date.date().weekday() == 6:
            calendar = SimpleCalendar()
            await callback.message.answer(
                f"{get_translation(lang, 'uncorrect_date')}\n"
                f"{get_translation(lang, 'select_admission_date')}",
                reply_markup=await calendar.start_calendar()
            )
            return
        
        selected_date = date.strftime(DateTimeFormats.ISO_DATE)
        service['registration_date'] = selected_date
        await state.update_data(service=service, step="")
        message_text = get_translation(lang, "select_admission_time")
        await handle_fetch_doctor_services(callback.message, state, message_text)


async def _handle_service_selection(callback: CallbackQuery, state: FSMContext):
    """Handle service selection for printing."""
    await callback.message.delete()
    await callback.answer()
    
    service_id = callback.data.split(CallbackData.PRINT_SERVICE_PREFIX)[1]
    state_data = await state.get_data()
    selected_services = state_data.get("selected_services_print", [])
    
    if service_id in selected_services:
        selected_services.remove(service_id)
    else:
        selected_services.append(service_id)
    
    await state.update_data(selected_services_print=selected_services)
    await handle_fetch_services(callback.message, state, True)
    await callback.answer()


async def _handle_doctor_selection(callback: CallbackQuery, state: FSMContext):
    """Handle doctor selection."""
    await callback.message.delete()
    await callback.answer()
    
    doctor_id = callback.data.split(CallbackData.ADMITTANCE_DOCTOR_PREFIX)[1]
    state_data = await state.get_data()
    fetched_doctors = state_data.get("fetched_doctors", [])
    service = state_data.get("service", {})
    
    current_doctor = next(
        (doc for doc in fetched_doctors if str(doc["id"]) == doctor_id),
        None
    )
    
    if current_doctor:
        service['doctor'] = current_doctor['id']
        service['doctor_obj'] = current_doctor
        await state.update_data(service=service, step=StateStep.REGISTRATION_DATE)
        
        calendar = SimpleCalendar()
        lang = state_data.get('language', Defaults.LANGUAGE)
        await callback.message.answer(
            get_translation(lang, 'select_admission_date'),
            reply_markup=await calendar.start_calendar()
        )
        await callback.answer()


async def _handle_admittance_type_selection(callback: CallbackQuery, state: FSMContext):
    """Handle admittance type selection."""
    await callback.message.delete()
    await callback.answer()
    
    adm_type_id = callback.data.split(CallbackData.ADMITTANCE_TYPE_PREFIX)[1]
    state_data = await state.get_data()
    service = state_data.get("service", {})
    fetched_admittance_type = state_data.get("fetched_admittanceType", [])
    
    current_adm_type = next(
        (adm for adm in fetched_admittance_type if str(adm["id"]) == adm_type_id),
        None
    )
    
    if current_adm_type:
        service['admittanceType'] = current_adm_type['id']
        service['admittanceType_obj'] = current_adm_type
        await state.update_data(service=service, step=StateStep.SERVICE_CONFIRM)
        confirm_kb = await get_confirm_keyboard(state)
        
        lang = state_data.get('language', Defaults.LANGUAGE)
        doctor_name = get_full_name(service.get('doctor_obj', {}))
        admittance_type = get_safe_attribute(service, 'admittanceType_obj.title')
        amount = float(get_safe_attribute(service, 'admittanceType_obj.amount', 0))
        time = service.get('registrationDate', '')
        
        message_text = (
            f"<b>{get_translation(lang, 'is_correct')}</b>\n"
            f"{get_translation(lang, 'doctor')}: {doctor_name}\n"
            f"{get_translation(lang, 'admittanceType')}: {admittance_type} - <b>{amount}</b>\n"
            f"{get_translation(lang, 'time')}: {time}"
        )
        
        await callback.message.answer(message_text, reply_markup=confirm_kb)
        await callback.answer()


async def _handle_time_selection(callback: CallbackQuery, state: FSMContext):
    """Handle time slot selection."""
    await callback.message.delete()
    await callback.answer()
    
    time_str = callback.data.split(CallbackData.SELECT_HOUR_PREFIX)[1]
    state_data = await state.get_data()
    service = state_data.get("service", {})
    
    registration_date = datetime.strptime(
        f"{service.get('registration_date', '')} {time_str}",
        f"{DateTimeFormats.ISO_DATE} {DateTimeFormats.TIME_SLOT}"
    )
    service['registrationDate'] = registration_date.isoformat()
    
    await state.update_data(service=service)
    await handle_fetch_admittance_type(callback.message, state)
    await callback.answer()


async def _handle_gender_selection(callback: CallbackQuery, state: FSMContext):
    """Handle gender selection."""
    await callback.message.delete()
    await callback.answer()
    
    state_data = await state.get_data()
    lang = state_data.get("language", Defaults.LANGUAGE)
    patient_form = state_data.get("patient_form", {})
    
    patient_form["gender"] = 1 if callback.data == CallbackData.MALE else 2
    await state.update_data(patient_form=patient_form, step=StateStep.BIRTHDAY)
    await callback.message.answer(get_translation(lang, "select_birthday"))


async def _handle_doctor_pagination(callback: CallbackQuery, state: FSMContext):
    """Handle doctor list pagination."""
    state_data = await state.get_data()
    await callback.message.delete()
    await callback.answer()
    
    offset = state_data.get("offset", Defaults.OFFSET)
    limit = state_data.get("limit", Defaults.LIMIT)
    
    if callback.data == CallbackData.DOCTOR_PREV:
        await state.update_data(offset=max(0, offset - limit))
    elif callback.data == CallbackData.DOCTOR_NEXT:
        await state.update_data(offset=offset + limit)
    
    await handle_fetch_doctors(callback.message, state)


async def _handle_admittance_type_pagination(callback: CallbackQuery, state: FSMContext):
    """Handle admittance type list pagination."""
    state_data = await state.get_data()
    await callback.message.delete()
    await callback.answer()
    
    offset = state_data.get("offset", Defaults.OFFSET)
    limit = state_data.get("limit", Defaults.LIMIT)
    
    if callback.data == CallbackData.ADMITTANCE_TYPE_PREV:
        await state.update_data(offset=max(0, offset - limit))
    elif callback.data == CallbackData.ADMITTANCE_TYPE_NEXT:
        await state.update_data(offset=offset + limit)
    
    await handle_fetch_admittance_type(callback.message, state)
