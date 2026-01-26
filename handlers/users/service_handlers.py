"""Handlers for service-related operations."""
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from utils.api_client import api_client
from utils.helpers import get_translation
from utils.constants import CallbackData, Defaults
from utils.state_helpers import get_state_data
from utils.message_helpers import loading_message, send_error_message
from keyboards.inline.main import get_come_back_keyboard
from services.keyboard_builder import KeyboardBuilder
from services.text_builder import TextBuilder


async def handle_fetch_services(
    message: Message,
    state: FSMContext,
    from_state: bool = False
):
    """Fetch and display services for the patient."""
    state_data = await get_state_data(state)
    lang = state_data.language
    patient_id = state_data.patient_id
    selected_services = state_data.selected_services_print
    fetched_services = state_data.fetched_services

    services = fetched_services if from_state else None

    if not from_state:
        async with loading_message(message, state) as _:
            try:
                services = await api_client.get_services_by_patient(patient_id)
                if services:
                    await state.update_data(fetched_services=services)
            except Exception:
                await send_error_message(message, state)
                return

    if services:
        services_list_kb = await KeyboardBuilder.build_services_keyboard(
            services, selected_services, lang
        )
        services_text = TextBuilder.build_services_text(services, selected_services)

        await message.answer(
            f"<b>{get_translation(lang, 'select_service')}</b> \n{services_text}",
            reply_markup=services_list_kb,
        )
    else:
        come_back_kb = await get_come_back_keyboard(state)
        await message.answer(
            get_translation(lang, 'empty_services'),
            reply_markup=come_back_kb,
        )


async def handle_fetch_doctors(message: Message, state: FSMContext):
    """Fetch and display doctors list."""
    state_data = await get_state_data(state)
    lang = state_data.language
    limit = state_data.limit
    offset = state_data.offset

    async with loading_message(message, state) as _:
        try:
            data = await api_client.get_doctors(
                role=Defaults.DOCTOR_ROLE,
                limit=limit,
                offset=offset
            )
            
            if data and data.get('results'):
                doctors = data['results']
                await state.update_data(
                    fetched_doctors=doctors,
                    count=data.get('count', 0)
                )
            else:
                doctors = []
        except Exception:
            await send_error_message(message, state)
            return

    if doctors:
        doctors_list_kb = await KeyboardBuilder.build_paginated_keyboard(
            doctors,
            CallbackData.ADMITTANCE_DOCTOR_PREFIX,
            state,
            lang,
            come_back_callback=CallbackData.COME_BACK_ADD_SERVICE
        )
        doctors_text = TextBuilder.build_doctors_text(doctors)

        await message.answer(
            f"<b>{get_translation(lang, 'select_doctor')}</b> \n{doctors_text}",
            reply_markup=doctors_list_kb,
        )
    else:
        come_back_kb = await get_come_back_keyboard(state, CallbackData.COME_BACK_ADD_SERVICE)
        await message.answer(
            get_translation(lang, 'empty_list'),
            reply_markup=come_back_kb,
        )


async def handle_fetch_admittance_type(message: Message, state: FSMContext):
    """Fetch and display admittance types for selected doctor."""
    state_data = await get_state_data(state)
    lang = state_data.language
    limit = state_data.limit
    doctor = state_data.service.get("doctor")
    offset = state_data.offset

    async with loading_message(message, state) as _:
        try:
            data = await api_client.get_admittance_types(
                doctor_id=doctor,
                limit=limit,
                offset=offset
            )
            
            if data and data.get('results'):
                admittance_types = data['results']
                await state.update_data(
                    fetched_admittanceType=admittance_types,
                    count=data.get('count', 0)
                )
            else:
                admittance_types = []
        except Exception:
            await send_error_message(message, state)
            return

    if admittance_types:
        admittance_type_kb = await KeyboardBuilder.build_paginated_keyboard(
            admittance_types,
            CallbackData.ADMITTANCE_TYPE_PREFIX,
            state,
            lang,
            come_back_callback=CallbackData.COME_BACK_ADD_SERVICE
        )
        admittance_type_text = TextBuilder.build_admittance_type_text(admittance_types)

        await message.answer(
            f"<b>{get_translation(lang, 'select_admittance_type')}</b> \n{admittance_type_text}",
            reply_markup=admittance_type_kb,
        )
    else:
        come_back_kb = await get_come_back_keyboard(state, CallbackData.COME_BACK_ADD_SERVICE)
        await message.answer(
            get_translation(lang, 'empty_list'),
            reply_markup=come_back_kb,
        )


async def handle_fetch_doctor_services(message: Message, state: FSMContext, msg: str = ""):
    """Fetch doctor timetable and display available time slots."""
    state_data = await get_state_data(state)
    lang = state_data.language
    doctor = state_data.service.get("doctor")
    registration_date = state_data.service.get("registration_date")

    async with loading_message(message, state) as _:
        try:
            timetable = await api_client.get_doctor_timetable(
                doctor_id=doctor,
                date=registration_date,
                is_confirmed=True
            )
            
            if timetable:
                services = timetable.get("services", [])
                reserves = timetable.get("reserves", [])
            else:
                services = []
                reserves = []
        except Exception:
            await send_error_message(message, state)
            return

    from services.time_slot_service import TimeSlotService
    from utils.constants import Defaults
    
    booked_times = TimeSlotService.get_blocked_half_hour_slots(reserves, services)
    
    buttons = KeyboardBuilder.build_hour_buttons(
        Defaults.WORK_START_HOUR,
        Defaults.WORK_END_HOUR,
        booked_times
    )
    
    await message.answer(msg, reply_markup=buttons)
