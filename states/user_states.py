"""FSM states for user interactions."""
from aiogram.fsm.state import State, StatesGroup


class UserState(StatesGroup):
    """User state machine states."""
    language = State()
    phone_number = State()
    patient_id = State()
    patient_guid = State()
    selected_services_print = State()
    fetched_services = State()
    patient_form = State()
    add_patient = State()
    step = State()
    cart = State()
    service = State()
    fetched_doctors = State()
    fetched_admittanceType = State()
    delete_services = State()
    limit = State()
    offset = State()
    count = State()
