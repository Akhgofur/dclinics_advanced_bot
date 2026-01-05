from itertools import count
from operator import add
import random
import os
import ssl
import asyncio
from typing import List, Set
import aiohttp
from aiogram import Router, F
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
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from environs import Env
from handlers.users.pdf import generate_pdf, generate_pdf_service
from keyboards.default.main import (
    get_request_contact_keyboard,
    get_services_print_keyboard,
)
from keyboards.inline.main import (
    get_add_service_keyboard,
    get_cart_keyboard,
    get_come_back_keyboard,
    get_confirm_keyboard,
    get_gender_keyboard,
    get_language_kb,
    get_today_keyboard,
)
from utils.helpers import get_full_name, get_safe_attribute, get_translation
from datetime import date, datetime, timedelta
import re
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from typing import List, Set, Dict



router = Router()
env = Env()
env.read_env()
BACK_END_URL = env.str("BACK_END_URL")


def get_ssl():
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    return ssl_context


# FSM States
class UserState(StatesGroup):
    language = State()
    phone_number = State()
    patient_id = State()
    patient_guid = State()
    selected_services_print = State([])
    fetched_services = State([])
    patient_form = State({})
    add_patient = State(False)
    step = State('')
    cart = State([])
    service = State({})
    fetched_doctors = State([])
    fetched_admittanceType = State([])
    delete_services = State([])
    
    limit = State(10)
    offset = State(0)
    count = State(0)
    # admittance_add = State({})


async def get_main_keyboard(state: FSMContext) -> InlineKeyboardMarkup:
    data = await state.get_data()
    lang = data.get("language", "ru")

    services = get_translation(lang, "services")
    add_service = get_translation(lang, "add_service")
    change_lang = get_translation(lang, "change_lang")

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=f"{services}",
                    # callback_data="services"
                ),
                KeyboardButton(
                    text=f"{add_service}",
                    # callback_data="add_service"
                ),
            ],
            [
                KeyboardButton(
                    text=f"{change_lang}",
                    # callback_data="change_lang"
                )
            ],
        ],
        resize_keyboard=True,
        # one_time_keyboard=True,
    )


# async def handle_start(message, callback, state):


# Handle contact
# @router.message(F.contact)


async def handle_language_request(message: Message, state: FSMContext):
    # await state.set_data()
    state_data = await state.get_data()
    lang = state_data.get("language", "ru")
    await message.answer(
        f"{get_translation(lang, 'select_lang')}", reply_markup=get_language_kb()
    )


async def handle_patient(message, state):
    data = await state.get_data()
    lang = data.get("language")
    patient_id = data.get("patient_id", None)
    patient_guid = data.get("patient_guid", None)

    if lang is None:
        await handle_language_request(message, state)

    elif patient_id:
        main_kb = await get_main_keyboard(state)
        await message.answer(
            f"{get_translation(lang, 'select_action')}", reply_markup=main_kb
        )

    else:
        
        await state.update_data(step='phone')
        request_contact_keyboard = await get_request_contact_keyboard(state)
        await message.answer(
            f"{get_translation(lang, 'request_number')}",
            reply_markup=request_contact_keyboard,
        )


async def handle_contact(message: Message, state: FSMContext, fromMessage = False):
    contact = message.contact
    
    if fromMessage:
        phone_number = message.text
    else: 
        phone_number = contact.phone_number
        
    # full_name = f"{contact.first_name} {contact.last_name or ''}"

    await state.update_data(phone_number=phone_number, step="")

    state_data = await state.get_data()

    lang = state_data.get("language", "ru")

    confirm_kb = await get_confirm_keyboard(state)

    await message.answer(
        f"{get_translation(lang, 'number_received')} {phone_number}",
        reply_markup=ReplyKeyboardRemove(),
    )
    loading_msg = await message.answer(get_translation(lang, "patient_finding"))

    patient = None

    ssl_context = get_ssl()
    timeout = aiohttp.ClientTimeout(total=10)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(
                f"{BACK_END_URL}/api/patient/?q={phone_number}", ssl=ssl_context
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data:
                        patient = data[0]
        except aiohttp.ClientError:
            await message.answer(get_translation(lang, 'try_again'))
            return
        except asyncio.TimeoutError:
            await message.answer(get_translation(lang, 'request_timeout'))
            return
        finally:
            await loading_msg.delete()

    if patient:
        await state.update_data(
            patient_id=patient["id"],
            patient_guid=patient["guid"],
            patient_first_name=patient["first_name"],
            patient_last_name=patient["last_name"],
        )
        await message.answer(
            f"{get_translation(lang, 'name')}: {get_full_name(patient)}\n{get_translation(lang, 'birthday')}: {get_safe_attribute(patient, 'birthday')}\n\n{get_translation(lang, 'is_your_data')}",
            reply_markup=confirm_kb,
        )
    
    else:
        
        await state.update_data(
            add_patient=True,
            patient_form={"phone": phone_number}
        )
        await message.answer(
            f"{get_translation(lang, 'record_not_found')}\n{get_translation(lang, 'write_name_for_registration')}\n{get_translation(lang, 'name_example')}",
            # reply_markup=confirm_kb,
        )




async def build_services_keyboard(data, selected_services=[], lang="ru"): 
    
    buttons = []

    # Create a button for each doctor
    for index, item in enumerate(data):
        button = InlineKeyboardButton(
            text=f"{index + 1}",
            callback_data=f"print_service_{item['id']}"
        )
        buttons.append(button)

    # Group buttons into rows of 5
    rows = [buttons[i:i + 5] for i in range(0, len(buttons), 5)]


    come_back = get_translation(lang, "come_back")
    print_results = get_translation(lang, "print_results")
    
    if len(selected_services) == 0:        
        rows.append(
            [InlineKeyboardButton(text=come_back, callback_data=f"come_back")],
        )
    
    else :
        rows.append([InlineKeyboardButton(text=come_back, callback_data=f"come_back"), InlineKeyboardButton(text=print_results, callback_data=f"print_results")])
        
                

    return InlineKeyboardMarkup(
        inline_keyboard=rows
    )


def build_services_text(data, selected_services=[]):
    content = ""

    for index, item in enumerate(data):
        dt = datetime.fromisoformat(get_safe_attribute(item, "registrationDate"))
        date_only = dt.strftime("%d.%m.%Y %H:%M")

        checked = "✅" if str(item["id"]) in selected_services else "❌"

        content += f"{index + 1}. {checked} {date_only} {get_safe_attribute(item, 'admittanceType.title')} - {get_full_name(get_safe_attribute(item, 'doctor'))} \n"

        # Each row has one button — wrap it in a list

    return content






async def handle_fetch_services(message: Message, state: FSMContext, from_state=False):

    state_data = await state.get_data()

    lang = state_data.get("language", "ru")
    patient_id = state_data.get("patient_id")
    selected_services = state_data.get("selected_services_print", [])
    fetched_services = state_data.get("fetched_services", [])


    services = None

    
    
    
    if from_state:
        services = fetched_services
    else:
        
        loading_msg = await message.answer(get_translation(lang, "loading"))
        ssl_context = get_ssl()
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.get(
                    f"{BACK_END_URL}/api/admittance-service/?patient={patient_id}&ordering=-registrationDate&isConfirmed=true",
                    ssl=ssl_context,
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data:
                            services = data
                            await state.update_data(fetched_services=data)
            except aiohttp.ClientError:
                await message.answer(get_translation(lang, 'try_again'))
                return
            except asyncio.TimeoutError:
                await message.answer(get_translation(lang, 'request_timeout'))
                return
            finally:
                await loading_msg.delete()

    if services:
        # await state.update_data(patient_id=services['id'], patient_guid=services['guid'], patient_first_name=services['first_name'], patient_last_name=services['last_name'])

        services_list_kb = await build_services_keyboard(services, selected_services, lang)

        services_text = build_services_text(services, selected_services)

        

        await message.answer(
            f"<b>{get_translation(lang, 'select_service')}</b> \n{services_text}",
            reply_markup=services_list_kb,
        )

        # await msg.delete()
    else:

        come_back_kb = await get_come_back_keyboard(state)
        await message.answer(
            f"{get_translation(lang, 'empty_services')}",
            reply_markup=come_back_kb,
        )





async def build_doctors_keyboard(data, state: FSMContext, lang="ru"):
    
    state_data = await state.get_data()
    count = state_data.get("count", 0)
    offset = state_data.get("offset", 0)
    limit = state_data.get("limit", 10)
    
    paginate_kb = [
        InlineKeyboardButton(text="<", callback_data="doctor_prev"),
        InlineKeyboardButton(text=">", callback_data="doctor_next"),
    ]
    
    
    if offset == 0 and count <= limit:
        paginate_kb = [
            
        ]
    elif offset == 0:
        paginate_kb = [
            InlineKeyboardButton(text=">", callback_data="doctor_next"),
        ]
    elif offset + limit >= count:
        paginate_kb = [
            InlineKeyboardButton(text="<", callback_data="doctor_prev"),
        ]
    
    
    
    
    buttons = []

    # Create a button for each doctor
    for index, item in enumerate(data):
        button = InlineKeyboardButton(
            text=f"{index + 1}",
            callback_data=f"admittance_doctor_{item['id']}"
        )
        buttons.append(button)

    # Group buttons into rows of 5
    rows = [buttons[i:i + 5] for i in range(0, len(buttons), 5)]

    # Add "come back" button in its own row
    come_back = get_translation(lang, "come_back")
    
    # if count > limit 
    if paginate_kb:
        rows.append(paginate_kb)
        
    rows.append(
        [
            InlineKeyboardButton(text=come_back, callback_data="come_back_add_service")
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_doctors_text(data):
    content = ""

    for index, item in enumerate(data):
        content += f"{index + 1}. {get_full_name(item)} {get_safe_attribute(item, 'speciality.title')}\n"
        # Each row has one button — wrap it in a list

    return content





async def build_admittanceType_keyboard(data, state: FSMContext, lang="ru"):
    
    state_data = await state.get_data()
    count = state_data.get("count", 0)
    offset = state_data.get("offset", 0)
    limit = state_data.get("limit", 10)
    
    paginate_kb = [
        InlineKeyboardButton(text="<", callback_data="admittanceType_prev"),
        InlineKeyboardButton(text=">", callback_data="admittanceType_next"),
    ]
    
    
    if offset == 0 and count <= limit:
        paginate_kb = [
            
        ]
    elif offset == 0:
        paginate_kb = [
            InlineKeyboardButton(text=">", callback_data="admittanceType_next"),
        ]
    elif offset + limit >= count:
        paginate_kb = [
            InlineKeyboardButton(text="<", callback_data="admittanceType_prev"),
        ]
    
    
    
    
    buttons = []

    # Create a button for each doctor
    for index, item in enumerate(data):
        button = InlineKeyboardButton(
            text=f"{index + 1}",
            callback_data=f"admittance_admittanceType_{item['id']}"
        )
        buttons.append(button)

    # Group buttons into rows of 5
    rows = [buttons[i:i + 5] for i in range(0, len(buttons), 5)]

    # Add "come back" button in its own row
    come_back = get_translation(lang, "come_back")
    
    # if count > limit 
    if paginate_kb:
        rows.append(paginate_kb)
        
    rows.append(
        [
            InlineKeyboardButton(text=come_back, callback_data="come_back_add_service")
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)




def build_admittanceType_text(data):
    content = ""

    for index, item in enumerate(data):
        content += f"{index + 1}. {get_safe_attribute(item, 'title')} - <b>{float(get_safe_attribute(item, 'amount'))}</b>\n"
        # Each row has one button — wrap it in a list

    return content




async def handle_fetch_doctors(message: Message, state: FSMContext):

    state_data = await state.get_data()

    lang = state_data.get("language", "ru")
    
    limit = state_data.get("limit", 10)
    offset = state_data.get("offset", 0)

    doctors = []

    
    loading_msg = await message.answer(get_translation(lang, "loading"))
    ssl_context = get_ssl()
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(
                f"{BACK_END_URL}/api/staff/?role=2&p=true&limit={limit}&offset={offset}",
                ssl=ssl_context,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['results']:
                        doctors = data['results']
                        await state.update_data(fetched_doctors=data['results'], count=data['count'])
        except aiohttp.ClientError:
            await message.answer(get_translation(lang, 'try_again'))
            return
        except asyncio.TimeoutError:
            await message.answer(get_translation(lang, 'request_timeout'))
            return
        finally:
            await loading_msg.delete()

    
    
    await state.update_data(fetched_doctors=doctors)
    if doctors:
        # await state.update_data(patient_id=services['id'], patient_guid=services['guid'], patient_first_name=services['first_name'], patient_last_name=services['last_name'])

        doctors_list_kb = await build_doctors_keyboard(doctors, state, lang)

        doctors_text = build_doctors_text(doctors)

        

        await message.answer(
            f"<b>{get_translation(lang, 'select_doctor')}</b> \n{doctors_text}",
            reply_markup=doctors_list_kb,
        )

        # await msg.delete()
    else:

        come_back_kb = await get_come_back_keyboard(state, 'come_back_add_service')
        await message.answer(
            f"{get_translation(lang, 'empty_list')}",
            reply_markup=come_back_kb,
        )




async def handle_fetch_admittanceType(message: Message, state: FSMContext):

    state_data = await state.get_data()

    lang = state_data.get("language", "ru")
    
    limit = state_data.get("limit", 10)
    doctor = state_data.get("service", {})["doctor"]
    offset = state_data.get("offset", 0)

    admittanceTypes = []

    
    loading_msg = await message.answer(get_translation(lang, "loading"))
    ssl_context = get_ssl()
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(
                f"{BACK_END_URL}/api/admittance-type/?p=true&limit={limit}&offset={offset}&user={doctor}&showBot=true",
                ssl=ssl_context,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['results']:
                        admittanceTypes = data['results']
                        await state.update_data(fetched_admittanceType=data['results'], count=data['count'])
        except aiohttp.ClientError:
            await message.answer(get_translation(lang, 'try_again'))
            return
        except asyncio.TimeoutError:
            await message.answer(get_translation(lang, 'request_timeout'))
            return
        finally:
            await loading_msg.delete()

    
    
    await state.update_data(fetched_admittanceType=admittanceTypes)
    if admittanceTypes:
        # await state.update_data(patient_id=services['id'], patient_guid=services['guid'], patient_first_name=services['first_name'], patient_last_name=services['last_name'])

        admittanceType_list_kb = await build_admittanceType_keyboard(admittanceTypes, state, lang)

        admittanceType_text = build_admittanceType_text(admittanceTypes)

        

        await message.answer(
            f"<b>{get_translation(lang, 'select_admittance_type')}</b> \n{admittanceType_text}",
            reply_markup=admittanceType_list_kb,
        )

        # await msg.delete()
    else:

        come_back_kb = await get_come_back_keyboard(state, 'come_back_add_service')
        await message.answer(
            f"{get_translation(lang, 'empty_list')}",
            reply_markup=come_back_kb,
        )
        


def _slot_label(dt: datetime) -> str:
    return f"{dt.hour:02d}:{'00' if dt.minute < 30 else '30'}"

def _overlapping_slots(start: datetime, end: datetime) -> Set[str]:
    # start at the floor to :00 or :30
    minute = 0 if start.minute < 30 else 30
    slot = start.replace(minute=minute, second=0, microsecond=0)
    if slot > start:
        slot -= timedelta(minutes=30)

    out = set()
    while slot < end:
        slot_end = slot + timedelta(minutes=30)
        # any intersection with [start, end)
        if slot_end > start and slot < end:
            out.add(f"{slot.hour:02d}:{'00' if slot.minute == 0 else '30'}")
        slot += timedelta(minutes=30)
    return out

def get_blocked_half_hour_slots(reserves: List[Dict], services: List[Dict]) -> Set[str]:
    blocked: Set[str] = set()

    # 1) block service registration half-hour slots
    for s in services:
        d = s.get("registrationDate")
        if d:
            try:
                dt = datetime.fromisoformat(d)
                blocked.add(_slot_label(dt))
            except Exception:
                pass

    # 2) block every half-hour that overlaps reserve periods
    for r in reserves:
        start, end = r.get("start"), r.get("end")
        if start and end:
            try:
                dt_start = datetime.fromisoformat(start)
                dt_end = datetime.fromisoformat(end)
                if dt_end > dt_start:
                    blocked |= _overlapping_slots(dt_start, dt_end)
            except Exception:
                pass

    return blocked




def build_hour_buttons(start_hour: int, end_hour: int, blocked_times: Set[str]) -> InlineKeyboardMarkup:
    """
    Builds an InlineKeyboardMarkup with times in HH:00 and HH:30 format,
    skipping buttons that are blocked.
    """
    if not (0 <= start_hour <= 23 and 0 <= end_hour <= 23 and start_hour <= end_hour):
        raise ValueError("start_hour and end_hour must be in range 0–23 and start <= end")

    inline_keyboard = []

    for hour in range(start_hour, end_hour + 1):
        row = []

        for minute in ["00", "30"]:
            time_str = f"{hour:02d}:{minute}"
            if time_str in blocked_times:
                continue  # 🔒 time is booked, skip
            row.append(
                InlineKeyboardButton(
                    text=time_str,
                    callback_data=f"select_hour:{time_str}"
                )
            )

        if row:
            inline_keyboard.append(row)

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def handle_fetch_doctor_services(message: Message, state: FSMContext, msg = ""):

    state_data = await state.get_data()

    lang = state_data.get("language")
    
    
    doctor = state_data.get("service", {})["doctor"]
    registration_date = state_data.get("service", {}).get("registration_date")

    services = []
    recerves = []
    
    loading_msg = await message.answer(get_translation(lang, "loading"))
    ssl_context = get_ssl()
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(
                f"{BACK_END_URL}/api/doctor-timetable/?doctor={doctor}&date={registration_date}&isConfirmed=true",
                ssl=ssl_context,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data:
                        services = data[0].get("services", [])
                        reserves = data[0].get("reserves", [])
                        
                        
        except aiohttp.ClientError:
            await message.answer(get_translation(lang, 'try_again'))
            return
        except asyncio.TimeoutError:
            await message.answer(get_translation(lang, 'request_timeout'))
            return
        finally:
            await loading_msg.delete()
            
    
    
    booked_times = get_blocked_half_hour_slots(reserves, services)
    
    
    buttons = build_hour_buttons(8, 17, booked_times)
    
    await message.answer(msg, reply_markup=buttons)

    
    


# def build_hour_buttons(start_hour: int, end_hour: int) -> InlineKeyboardMarkup:
#     if not (0 <= start_hour <= 23 and 0 <= end_hour <= 23 and start_hour <= end_hour):
#         raise ValueError("start_hour and end_hour must be in range 0–23 and start <= end")

#     inline_keyboard = []

#     for hour in range(start_hour, end_hour + 1):
#         row = [
#             InlineKeyboardButton(text=f"{hour:02d}:00", callback_data=f"select_hour:{hour:02d}:00"),
#             InlineKeyboardButton(text=f"{hour:02d}:30", callback_data=f"select_hour:{hour:02d}:30"),
#         ]
#         inline_keyboard.append(row)

#     return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)





async def process_confirmation(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    phone = user_data.get("phone_number")
    lang = user_data.get("language")
    

    if callback.data == "confirm_yes":
        main_kb = await get_main_keyboard(state)
        await callback.message.answer(
            f"✅ {get_translation(lang, 'confirmed')}: {phone}", reply_markup=main_kb
        )

    else:
        await state.update_data(patient_guid=None)
        await state.update_data(patient_id=None)
        await state.update_data(patient_first_name=None)
        await state.update_data(patient_last_name=None)

        # await callback.message.answer(f"❌ {}")

        # await callback.message.edit_reply_markup()
        await callback.answer()
        
        await state.update_data(
            add_patient=True,
            patient_form={"phone": phone}
        )
        await callback.message.answer(
            f"{get_translation(lang, 'write_name_for_registration')}\n{get_translation(lang, 'name_example')}",
            # reply_markup=confirm_kb,
        )



async def process_patient_add_confirmation(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    # phone = user_data.get("phone_number")
    lang = user_data.get("language")

    if callback.data == "confirm_yes":
        
        await handle_post_patient(callback.message, state)
        

    else:
        await state.update_data(
            add_patient=True,
            step=""
        )
        await callback.message.answer(
            f"{get_translation(lang, 'write_name_for_registration')}\n{get_translation(lang, 'name_example')}",
            # reply_markup=confirm_kb,
        )
        # await callback.message.answer(f"❌ {}")

        await callback.message.edit_reply_markup()
        await callback.answer()
        
 
 
 
def build_cart_text(data, lang='ru'):
    content = ""
    
    if not data:
        return get_translation(lang, "empty_cart")
    
    
        
    total_amount_cart = 0
    total_quantity_cart = 0
    for index, item in enumerate(data):
        total_quantity_cart+=1
        total_amount_cart += float(get_safe_attribute(item, 'admittanceType_obj.amount', 0))
        content += f"{index + 1}. <b>{get_full_name(get_safe_attribute(item, 'doctor_obj', {}))}</b> - {get_safe_attribute(item, 'admittanceType_obj.title')} {get_safe_attribute(item, 'registrationDate')} <b>{get_safe_attribute(item, 'admittanceType_obj.amount', 0, True)}</b>\n"
        # Each row has one button — wrap it in a list

    
    content += f"\n\n<b>{get_translation(lang, 'total_quantity')}: {total_quantity_cart}</b> \n"
    content += f"<b>{get_translation(lang, 'total_amount')}: {total_amount_cart}</b> \n"
    return content


 
async def handle_open_cart(callback: CallbackQuery, state: FSMContext, additional_text=""):
    user_data = await state.get_data()
    
    lang = user_data.get("language")
    
    cart_services = user_data.get("cart", [])
    
    
    cart_text = build_cart_text(cart_services, lang)
    
    
    
    message = f"{additional_text}<b>{get_translation(lang, 'cart_services')}</b>\n\n{cart_text}"
    
    await callback.message.answer(
        message,
        reply_markup=await get_cart_keyboard(state)
    )
    
    

    
        
 
        
async def handle_post_patient(message: Message, state: FSMContext):
    
    ssl_context = get_ssl()

    timeout = aiohttp.ClientTimeout(total=10)

    guid = None
    patient_name = None
    async with aiohttp.ClientSession(timeout=timeout) as session:
        state_data = await state.get_data()
        lang = state_data.get('language', 'ru')
        
        loading_msg = await message.answer(
            f"{get_translation(lang, 'loading')}",
        )
        try:
            
            patient_data = state_data.get("patient_form", {})
            url = f"{BACK_END_URL}/api/patient/"
            
            
            async with session.post(url, ssl=ssl_context, data=patient_data) as response:
                if response.status in [200, 201, 204]:
                    data = await response.json()
                    if data:
                        
                        # print(data)

                        guid = data["guid"]
                        patient_name = f"{data['first_name']} {data['last_name']}"
                        await state.update_data(
                            patient_id=data["id"],
                            patient_guid=guid,
                            patient_first_name=data["first_name"],
                            patient_last_name=data["last_name"],
                            add_patient=False,
                            step="",
                        )
                        await message.answer(
                            f"{get_translation(lang, 'confirmed')}: {patient_name}",
                            reply_markup=await get_main_keyboard(state),
                        )
                        
                        patient_form = state_data.get("patient_form", {})
                        phone = state_data.get("phone", "")
                        patient_form["phone"] = phone
                        
                        main_kb = await get_main_keyboard(state)
                        await message.answer(
                            f"✅ {get_translation(lang, 'confirmed')}: {phone}", reply_markup=main_kb
                        )
        except aiohttp.ClientError:
            print("aiohttp.ClientError")
            await message.answer(get_translation(lang, 'try_again'))
            await state.update_data(
                add_patient=True,
                step=""
            )
            await message.answer(
                f"{get_translation(lang, 'write_name_for_registration')}\n{get_translation(lang, 'name_example')}",
                # reply_markup=confirm_kb,
            )

            return
        except asyncio.TimeoutError:
            print("asyncio.TimeoutError")
            await message.answer(get_translation(lang, 'request_timeout'))
            await state.update_data(
                add_patient=True,
                step=""
            )
            await message.answer(
                f"{get_translation(lang, 'write_name_for_registration')}\n{get_translation(lang, 'name_example')}",
                # reply_markup=confirm_kb,
            )
            return
        
        except Exception as e:
            print("Error", e)
            await message.answer(get_translation(lang, 'try_again'))
            await state.update_data(
                add_patient=True,
                step=""
            )
            
            await message.answer(
                f"{get_translation(lang, 'write_name_for_registration')}\n{get_translation(lang, 'name_example')}",
                # reply_markup=confirm_kb,
            )
       
            return
        finally:
            await loading_msg.delete()




   
async def handle_post_admittance(message: Message, state: FSMContext):
    
    ssl_context = get_ssl()

    timeout = aiohttp.ClientTimeout(total=10)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        state_data = await state.get_data()
        
        lang = state_data.get('language', 'ru')
        
        loading_msg = await message.answer(
            f"{get_translation(lang, 'loading')}",
        )
        try:
            
            cart = state_data.get("cart", [])
            
            if not cart:
                await handle_open_cart(message, state)
                return
            
            
            services = []
            
            
            for item in cart:
                service = {
                    "doctor": get_safe_attribute(item, "doctor"),
                    "admittanceType": get_safe_attribute(item, "admittanceType"),
                    "registrationDate": get_safe_attribute(item, "registrationDate"),
                    'quantity': 1,
                    'patient': get_safe_attribute(state_data, "patient_id"),
                    'amount' : float(get_safe_attribute(item, 'admittanceType_obj.amount', 0)),
                    'totalAmount' : float(get_safe_attribute(item, 'admittanceType_obj.amount', 0) * 1),
                    'paidAmount' : float(get_safe_attribute(item, 'admittanceType_obj.amount', 0) * 1),
                    # 'paidAmount' : float(get_safe_attribute(item, 'admittanceType_obj.price', 0) * 1),
                    'isCome': False,
                    'preBooking': True
                }
                services.append(service)
            
            
            admittance = {
                "patient": state_data.get("patient_id"),
                "registrationDate" : datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "services": list(services),
                'source': 2
            }
            
            
            # print(admittance)
            
            url = f"{BACK_END_URL}/api/admittance/"
            
            
            async with session.post(url, ssl=ssl_context, json=admittance) as response:
                
                # print(await response.json())
                if response.status in [200, 201, 204]:
                    data = await response.json()
                    if data:
                        
                        # print(data)
                        
                        await state.update_data(
                            cart=[],
                            service={}
                        )
                        
                        await message.answer(
                            f"{get_translation(lang, 'service_saved')}",
                            reply_markup=await get_main_keyboard(state),
                        )
                        
                    
        except aiohttp.ClientError:
            print("aiohttp.ClientError")
            await message.answer(get_translation(lang, 'try_again'))
            return
        except asyncio.TimeoutError:
            print("asyncio.TimeoutError")
            await message.answer(get_translation(lang, 'request_timeout'))
            return
        except Exception as e:
            print(f"Exception: {e}")
            await message.answer(get_translation(lang, 'error_try'))
            return
        
        finally:
            await loading_msg.delete()




async def handle_language(callback: CallbackQuery, state: FSMContext):
    await state.update_data(language=callback.data)
    await callback.answer()
    await handle_patient(callback.message, state)


# Start command
@router.message()
async def start(message: Message, state: FSMContext):
    # await state.set_data()
    
    
    print(message.text)

    data = await state.get_data()
    lang = data.get("language", "ru")
    patient_id = data.get("patient_id", None)
    patient_guid = data.get("patient_guid", None)
    step = data.get("step", "")

    services = get_translation(lang, "services")
    add_service = get_translation(lang, "add_service")
    change_lang = get_translation(lang, "change_lang")


    add_patient = data.get("add_patient", False)
    phone_number = data.get("phone_number", "")
    
    
    if add_patient and phone_number and step != "birthday":
        
        message_text = message.text.split(" ")
        
        service = data.get("patient_form", {})
        if len(message_text) < 2:
            await message.answer(
                f"{get_translation(lang, 'write_name_for_registration')}\n{get_translation(lang, 'name_example')}",
                reply_markup=ReplyKeyboardRemove(),
            )
            return
        first_name = message_text[0]
        last_name = message_text[1]
        
        
        if not service:
            service = {"phone": phone_number}
            
        service["first_name"] = first_name
        service["last_name"] = last_name
        
        
        await state.update_data(patient_form=service)
        gender_kb = await get_gender_keyboard(state)
        await message.answer(
            f"{get_translation(lang, 'select_gender')}",
            reply_markup=gender_kb,
        )
        
    
    elif message.text is not None and message.text.startswith('/start ') and len(message.text.split(" ")) == 2:
        await handle_code(message, state, customCode=message.text.split(" ")[1])
    
    # elif message.text is not None and re.match(r"^\d+$", message.text):
    #     await handle_code(message, state, message.text)
        
    elif message.text == "/start":

        await message.answer(
            f"{get_translation(lang, 'welcome')}",
            reply_markup=ReplyKeyboardRemove(),
        )
        await handle_patient(message, state)

    elif message.text == "/reset":

        # ReplyKeyboardRemove()

        await message.answer(
            f"{get_translation(lang, 'reset')}",
            reply_markup=ReplyKeyboardRemove(),
        )

        await state.clear()
        # if lang is None:
        await handle_language_request(message, state)

    elif message.contact and step == 'phone':
        await handle_contact(message, state)
    elif message.text and step == 'phone':
        await handle_contact(message, state, True)

    elif message.text == services:
       
        services_print_kb = await get_services_print_keyboard(state)
        await handle_fetch_services(message, state)

      

    elif message.text == add_service:
        data = await state.get_data()
        lang = data.get("language", "ru")
        add_service_text = get_translation(lang, "add_serv")
        add_service_kb = await get_add_service_keyboard(state)
        await message.answer(add_service_text, reply_markup=add_service_kb)

    elif message.text == change_lang:
        await handle_language_request(message, state)
    
    
    elif step == "birthday":

        # await callback.message.delete()
        # await callback.answer()  # Optional: acknowledge the button press

        state_data = await state.get_data()
        lang = state_data.get("language", "ru")
        service = state_data.get("patient_form", {})
        
        try:
            day, month, year = message.text.split(".")
            print(day, month, year)
            if not (day.isdigit() and month.isdigit() and year.isdigit()):
                await message.answer(f"{get_translation(lang, 'select_birthday')}")
                return
            selected_date = "-".join([year, month, day])
            
            
            service['birthday'] = selected_date
            await state.update_data(patient_form=service, step="check_data")
            gender_text = 'male' if service.get('gender', '') == 1 else 'female'
            message_text = f"<b>{get_translation(lang, "is_correct")}:</b>\n{get_translation(lang, "name")}: {service.get('first_name', '')} {service.get('last_name', '')}\n{get_translation(lang, 'phone')}: {service.get('phone', '')}\n{get_translation(lang, 'birthday')}: {selected_date}\n{get_translation(lang, 'gender')}: {get_translation(lang, gender_text)}"
            await message.answer(message_text, reply_markup=await get_confirm_keyboard(state))
            
        
        
            # await callback.answer()
        except Exception as e:
           
            await message.answer(f"{get_translation(lang, "select_birthday")}")
        
        
    elif step == "registrationDate":

        # await callback.message.delete()
        # await callback.answer()  # Optional: acknowledge the button press

        state_data = await state.get_data()
        lang = state_data.get("language", "ru")
        service = state_data.get("service", {})
        
        try:
            day, month, year = message.text.split(".")
            print(day, month, year)
            if not (day.isdigit() and month.isdigit() and year.isdigit()):
                today_kb = await get_today_keyboard(state)
                await message.answer(f"{get_translation(lang, 'select_admission_date')}", reply_markup=today_kb)
                return
            
            
            selected_date = "-".join([year, month, day])
            
            
            service['registration_date'] = selected_date
            await state.update_data(service=service, step="")
            message_text = f"{get_translation(lang, "select_admission_time")}"
            # await message.answer(message_text, reply_markup=build_hour_buttons(7, 18))
            await handle_fetch_doctor_services(message, state, message_text)
            
            
        
        
            # await callback.answer()
        except Exception as e:
            print(e)
            today_kb = await get_today_keyboard(state)
            await message.answer(f"{get_translation(lang, "select_admission_date")}", reply_markup=today_kb)
        
        
    
    
    


# # Start command
@router.callback_query()
async def handle_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    add_patient = data.get("add_patient", False)
    step = data.get("step")
    
    print("CALBACCCCCCCCCCCCCCCCKKKKKK", callback.data)

    if callback.data in ["uz", "ru", "en"]:
        await handle_language(callback, state)

    elif callback.data in ["confirm_yes", "confirm_no"] and not add_patient and step != "service_confirm":
        await callback.message.delete()
        await callback.answer()  
        await process_confirmation(callback, state)
        
    # elif callback.data and callback.data.startswith("simple_calendar:"):
        # parsed_data = SimpleCalendarCallbackData.parse(callback.data)  # ✅ this is key
        # selected, date = await SimpleCalendar().process_selection(callback, callback.data)
        
        
        # print(selected, 'selected')

        # if selected:
        #     # action=4, user selected a date
        #     await callback.message.edit_text(f"✅ Вы выбрали дату: {date.strftime('%Y-%m-%d')}")
        # else:
        #     # action in [2, 3, 5, 6], just update calendar
        #     await callback.answer()

        # return
    
    elif callback.data in ["confirm_yes", "confirm_no"] and add_patient and step != "service_confirm":
        await callback.message.delete()
        await callback.answer()  
        await process_patient_add_confirmation(callback, state)
        
    elif callback.data == "come_back_add_service":
        await callback.message.delete()
        await callback.answer()  
        data = await state.get_data()
        lang = data.get("language", "ru")
        add_service_text = get_translation(lang, "add_serv")
        add_service_kb = await get_add_service_keyboard(state)
        await callback.message.answer(add_service_text, reply_markup=add_service_kb)
    
    
    if callback.data.startswith("simple_calendar:"):
        selected, date = await SimpleCalendar().process_selection(
            callback,
            SimpleCalendarCallback.unpack(callback.data)
        )
        
        if 'CANCEL' in callback.data:
            await callback.message.delete()
            await callback.answer()
            await handle_fetch_doctors(callback.message, state)
        
        elif "TODAY" in callback.data:
            await callback.message.delete()
            await callback.answer()  # Optional: acknowledge the button press

            state_data = await state.get_data()
            lang = state_data.get("language", "ru")
            service = state_data.get("service", {})
        
            selected_date = datetime.now().strftime("%Y-%m-%d")
                
            service['registration_date'] = selected_date
            await state.update_data(service=service, step="")
            message_text = f"{get_translation(lang, "select_admission_time")}"
            # await callback.message.answer(message_text, reply_markup=build_hour_buttons(7, 18))
            await handle_fetch_doctor_services(callback.message, state, message_text)
        
        if selected:
            # await callback.message.answer(f"You selected: {date.strftime('%Y-%m-%d')}")
            await callback.message.delete()
            await callback.answer()  # Optional: acknowledge the button press

            state_data = await state.get_data()
            lang = state_data.get("language", "ru")
            service = state_data.get("service", {})
            
            if date.date() < datetime.now().date() or date.date().weekday() == 6:
                calendar = SimpleCalendar()
                await callback.message.answer(f"{get_translation(lang, 'uncorrect_date')}\n{get_translation(lang, 'select_admission_date')}", reply_markup=await calendar.start_calendar())
                
                return
        
            selected_date = date.strftime('%Y-%m-%d')
                
                
            service['registration_date'] = selected_date
            await state.update_data(service=service, step="")
            message_text = f"{get_translation(lang, "select_admission_time")}"
            # await callback.message.answer(message_text, reply_markup=build_hour_buttons(7, 18))
            await handle_fetch_doctor_services(callback.message, state, message_text)
            return
    
    elif step == "registrationDate" and callback.data == "today":

        await callback.message.delete()
        await callback.answer()  # Optional: acknowledge the button press

        state_data = await state.get_data()
        lang = state_data.get("language", "ru")
        service = state_data.get("service", {})
       
        selected_date = datetime.now().strftime("%Y-%m-%d")
        
            
            
        service['registration_date'] = selected_date
        await state.update_data(service=service, step="")
        message_text = f"{get_translation(lang, "select_admission_time")}"
        # await callback.message.answer(message_text, reply_markup=build_hour_buttons(7, 18))
        await handle_fetch_doctor_services(callback.message, state, message_text)
            
    
    
    
    elif step == "service_confirm":
        await callback.message.delete()
        await callback.answer()
        
        if callback.data == "confirm_yes":
            data = await state.get_data()
            cart = data.get("cart", [])
            service = data.get("service", {})
            cart.append(service)
            
            await state.update_data(service={}, step="", cart=cart)
            lang = data.get("language", "ru")
            # add_service_text = get_translation(lang, "add_serv")
            # add_service_kb = await get_add_service_keyboard(state)
            await callback.message.answer(f"{get_translation(lang, "added_to_cart")}")
            await handle_open_cart(callback, state)
        
        elif callback.data == "confirm_no":
            await state.update_data(service={}, step="")
            data = await state.get_data()
            lang = data.get("language", "ru")
            await callback.message.answer(f"{get_translation(lang, "canceled")}")
            await handle_open_cart(callback, state)
            return
        
        
        
        # await process_patient_add_confirmation(callback, state)
        
        
    elif callback.data == "change_lang":
        await callback.message.delete()
        await callback.answer()  
        
        await handle_language_request(callback.message, state)
        
    elif callback.data == "save_admittance":
        await callback.message.delete()
        await callback.answer()  
        
        await handle_post_admittance(callback.message, state)

    elif callback.data == "clear_cart":
        await callback.message.delete()
        await callback.answer()  
        await state.update_data(cart=[])
        state_data = await state.get_data()
        await handle_open_cart(callback, state, get_translation(state_data.get("language", "ru"), "cart_cleared"))

    elif callback.data == "come_back":
        # await callback.message.answer(get_translation(lang, "come_back"))
        # await callback.answer()
        await callback.message.delete()
        await callback.answer()  
        await state.update_data(selected_services_print=[])
        await handle_patient(callback.message, state)

    elif callback.data == "print_results":
        # await callback.message.answer(get_translation(lang, "come_back"))
        # await callback.answer()
        await callback.message.delete()
        await callback.answer()  
        await handle_code(callback.message, state, customCode=None, service=True)
        await state.update_data(selected_services_print=[])
        await handle_patient(callback.message, state)

    elif re.match(r"^\d+$", callback.data):
        await handle_code(callback.message, state, callback.data)

    elif callback.data.startswith("print_service_"):

        await callback.message.delete()
        await callback.answer()  # Optional: acknowledge the button press

        doctor_id = callback.data.split("print_service_")[1]
        state_data = await state.get_data()
        fetched_doctors = state_data.get("selected_services_print", [])

        if doctor_id in fetched_doctors:
            fetched_doctors.remove(doctor_id)
        else:
            fetched_doctors.append(doctor_id)

        await state.update_data(selected_services_print=fetched_doctors)

        # Fetch updated services
        await handle_fetch_services(callback.message, state, True)

        await callback.answer()
    
    elif callback.data.startswith("select_hour:"):

        await callback.message.delete()
        await callback.answer()  # Optional: acknowledge the button press

        time = callback.data.split("select_hour:")[1]
        state_data = await state.get_data()
        service = state_data.get("service", {})

        registrationDate = datetime.strptime(f"{service.get('registration_date', '')} {time}", "%Y-%m-%d %H:%M")
        service['registrationDate'] = registrationDate.isoformat()
        
        await state.update_data(service=service)
        
        await handle_fetch_admittanceType(callback.message, state)

        await callback.answer()
    
    
    elif callback.data.startswith("admittance_doctor_"):

        await callback.message.delete()
        await callback.answer()  # Optional: acknowledge the button press

        doctor_id = callback.data.split("admittance_doctor_")[1]
        state_data = await state.get_data()
        fetched_doctors = state_data.get("fetched_doctors", [])
        service = state_data.get("service", {})

        
        current_doctor = None
        for doctor in fetched_doctors:
            if str(doctor["id"]) == doctor_id:
                current_doctor = doctor
                break
        
        # if current_doctor:
        service['doctor'] = current_doctor['id']
        service['doctor_obj'] = current_doctor
        

        await state.update_data(service=service, step="registrationDate")
        
       
        calendar = SimpleCalendar()
        await callback.message.answer(f"{get_translation(state_data.get('language', 'ru'), 'select_admission_date')}", reply_markup=await calendar.start_calendar())
        await callback.answer()
        
    
    elif callback.data.startswith("admittance_admittanceType_"):

        await callback.message.delete()
        await callback.answer()  # Optional: acknowledge the button press

        adm_type_id = callback.data.split("admittance_admittanceType_")[1]
        state_data = await state.get_data()
        service = state_data.get("service", {})
        fetched_admittanceType = state_data.get("fetched_admittanceType", [])

        
        current_admType = None
        for adm_type in fetched_admittanceType:
            if str(adm_type["id"]) == adm_type_id:
                current_admType= adm_type
                break
        
        # if current_doctor:
        service['admittanceType'] = current_admType['id']
        service['admittanceType_obj'] = current_admType
        

        await state.update_data(service=service, step="service_confirm")
        confirm_kb = await get_confirm_keyboard(state)
        
        
        
        message_text = f"<b>{get_translation(state_data.get('language', 'ru'), 'is_correct')}</b>\n{get_translation(state_data.get('language', 'ru'), 'doctor')}: {get_full_name(service.get('doctor_obj', {}))}\n{get_translation(state_data.get('language', 'ru'), 'admittanceType')}: {get_safe_attribute(service, 'admittanceType_obj.title')} - <b>{float(get_safe_attribute(service, 'admittanceType_obj.amount'))}</b> \n{get_translation(state_data.get('language', 'ru'), 'time')}: {service.get('registrationDate', '')}"
        
        await callback.message.answer(f"{message_text}", reply_markup=confirm_kb)

        await callback.answer()
        
    elif callback.data in ["male", 'female']:

        await callback.message.delete()
        await callback.answer()  # Optional: acknowledge the button press

        state_data = await state.get_data()
        lang = state_data.get("language", "ru")
        patient_form = state_data.get("patient_form", {})
        
        

        if callback.data == 'male':
            patient_form["gender"] = 1
        else: 
            patient_form["gender"] = 2
        
        await state.update_data(patient_form=patient_form, step="birthday")
        
        
        # calendar = SimpleCalendar()
        await callback.message.answer(f"{get_translation(lang, "select_birthday")}")
        
    elif callback.data == 'cart':

        await callback.message.delete()
        await callback.answer()  # Optional: acknowledge the button press

        state_data = await state.get_data()
        lang = state_data.get("language", "ru")
        patient_form = state_data.get("patient_form", {})
        
        await handle_open_cart(callback, state)
        
        

        # if callback.data == 'male':
        #     patient_form["gender"] = 1
        # else: 
        #     patient_form["gender"] = 2
        
        # await state.update_data(patient_form=patient_form, step="birthday")
        
        
        # # calendar = SimpleCalendar()
        # await callback.message.answer(f"{get_translation(lang, "select_birthday")}")
        
    elif callback.data == "add_service":

        await callback.message.delete()
        await callback.answer()  # Optional: acknowledge the button press

        state_data = await state.get_data()
        lang = state_data.get("language", "ru")
        # patient_form = state _data.get("patient_form", {})
        
        await state.update_data(service={}, limit=10, offset=0, count=0)
        
        await handle_fetch_doctors(callback.message, state)
    
    elif callback.data in ["doctor_prev", "doctor_next"]:
        state_data = await state.get_data()
        await callback.message.delete()
        await callback.answer()  # Optional: acknowledge the button pres
        # patient_form = state _data.get("patient_form", {})
        
        if callback.data == "doctor_prev":
            await state.update_data(offset=state_data.get("offset", 0) - state_data.get("limit", 10))
        elif callback.data == "doctor_next":
            await state.update_data(offset=state_data.get("offset", 0) + state_data.get("limit", 10))
        
        
        
        await handle_fetch_doctors(callback.message, state)
    
    elif callback.data in ["admittanceType_prev", "admittanceType_next"]:
        state_data = await state.get_data()
        await callback.message.delete()
        await callback.answer()  # Optional: acknowledge the button pres
        # patient_form = state _data.get("patient_form", {})
        
        if callback.data == "admittanceType_prev":
            await state.update_data(offset=state_data.get("offset", 0) - state_data.get("limit", 10))
        elif callback.data == "admittanceType_next":
            await state.update_data(offset=state_data.get("offset", 0) + state_data.get("limit", 10))
        
        
        
        await handle_fetch_admittanceType(callback.message, state)
        
        
        
        
        
# @router.callback_query(simple_cal_callback.filter())
# async def cal_handler(callback: CallbackQuery, callback_data: dict):
    
#     print(callback_data, "callback_data")
#     selected, date = await SimpleCalendar().process_selection(
#         callback, callback_data
#     )
#     if selected:
#         await callback.message.edit_text(f"✅ Selected: {date}")
#     else:
#         await callback.answer()      

        


# Handle numeric code (PDF generation)
# @router.message(F.text.regexp(r"^\d+$"))
async def handle_code(message: Message, state, customCode=None, service=False):
    print(message.text, 'code_inside')
    data = await state.get_data()
    lang = data.get("language", 'ru')
    selected_services_print = data.get("selected_services_print", [])

    selected_services_print = ",".join(selected_services_print)

    code = message.text

    if customCode:
        code = customCode
    await message.answer(get_translation(lang, 'finding_results'))
    
    print(code, "code")

    ssl_context = get_ssl()

    timeout = aiohttp.ClientTimeout(total=10)

    guid = None
    patient_name = None
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:

            url = (
                f"{BACK_END_URL}/api/admittance/?q={code}"
                if not service
                else f"{BACK_END_URL}/api/admittance-service/chosen?id={selected_services_print}"
            )
            async with session.get(url, ssl=ssl_context) as response:
                if response.status == 200:
                    data = await response.json()
                    if data:

                        if service:
                            current_obj = data[0]
                            patient_name = f"{current_obj['patient']['first_name']} {current_obj['patient']['last_name']}"
                        else:
                            current_obj = data[0]
                            guid = current_obj["guid"]
                            patient_name = f"{current_obj['patient']['first_name']} {current_obj['patient']['last_name']}"
        except aiohttp.ClientError:
            print("aiohttp.ClientError")
            await message.answer(get_translation(lang, 'try_again'))
            return
        except asyncio.TimeoutError:
            print("asyncio.TimeoutError")
            await message.answer(get_translation(lang, 'request_timeout'))
            return

    if service:
        if not selected_services_print or not patient_name:
            await message.answer(get_translation(lang, 'not_found'))
            return

    else:
        if not guid or not patient_name:
            await message.answer(get_translation(lang, 'not_found'))
            return

    pdf_path = f"{patient_name}.pdf"

    if service:
        await generate_pdf_service(selected_services_print, pdf_path)

    else:
        await generate_pdf(guid, pdf_path)

    try:
        await message.answer_document(document=FSInputFile(pdf_path))
        os.remove(pdf_path)
    except Exception as e:
        print(e)
        await message.answer(get_translation(lang, 'pdf_not_generated'))


# Fallback
# @router.message(F.text)
# async def fallback(message: Message):
#     await message.answer("Iltimos, telefon raqamingizni yuboring yoki kodni kiriting.")
