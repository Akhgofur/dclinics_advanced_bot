"""Constants used throughout the application."""
from typing import Dict, List

# Callback data constants
class CallbackData:
    """Callback data strings used in inline keyboards."""
    # Language
    LANG_UZ = "uz"
    LANG_RU = "ru"
    LANG_EN = "en"
    
    # Confirmation
    CONFIRM_YES = "confirm_yes"
    CONFIRM_NO = "confirm_no"
    
    # Navigation
    COME_BACK = "come_back"
    COME_BACK_ADD_SERVICE = "come_back_add_service"
    
    # Services
    ADD_SERVICE = "add_service"
    PRINT_RESULTS = "print_results"
    PRINT_SERVICE_PREFIX = "print_service_"
    
    # Cart
    CART = "cart"
    SAVE_ADMITTANCE = "save_admittance"
    CLEAR_CART = "clear_cart"
    DELETE_SERVICE = "delete_service"
    
    # Doctor selection
    ADMITTANCE_DOCTOR_PREFIX = "admittance_doctor_"
    DOCTOR_PREV = "doctor_prev"
    DOCTOR_NEXT = "doctor_next"
    
    # Admittance type
    ADMITTANCE_TYPE_PREFIX = "admittance_admittanceType_"
    ADMITTANCE_TYPE_PREV = "admittanceType_prev"
    ADMITTANCE_TYPE_NEXT = "admittanceType_next"
    
    # Time selection
    SELECT_HOUR_PREFIX = "select_hour:"
    
    # Gender
    MALE = "male"
    FEMALE = "female"
    
    # Calendar
    TODAY = "today"
    SIMPLE_CALENDAR_PREFIX = "simple_calendar:"
    CANCEL = "CANCEL"
    
    # Other
    CHANGE_LANG = "change_lang"


# State step constants
class StateStep:
    """FSM state step values."""
    PHONE = "phone"
    BIRTHDAY = "birthday"
    REGISTRATION_DATE = "registrationDate"
    SERVICE_CONFIRM = "service_confirm"
    CHECK_DATA = "check_data"


# Default values
class Defaults:
    """Default values used in the application."""
    LANGUAGE = "ru"
    LIMIT = 10
    OFFSET = 0
    COUNT = 0
    DOCTOR_ROLE = 2
    WORK_START_HOUR = 8
    WORK_END_HOUR = 17
    SLOT_DURATION_MINUTES = 30


# API endpoints
class APIEndpoints:
    """API endpoint paths."""
    PATIENT = "/api/patient/"
    ADMITTANCE = "/api/admittance/"
    ADMITTANCE_SERVICE = "/api/admittance-service/"
    STAFF = "/api/staff/"
    ADMITTANCE_TYPE = "/api/admittance-type/"
    DOCTOR_TIMETABLE = "/api/doctor-timetable/"


# Date/Time formats
class DateTimeFormats:
    """Date and time format strings."""
    DISPLAY_DATE_TIME = "%d.%m.%Y %H:%M"
    ISO_DATE = "%Y-%m-%d"
    ISO_DATETIME = "%Y-%m-%dT%H:%M:%S"
    TIME_SLOT = "%H:%M"
    BIRTHDAY_INPUT = "%d.%m.%Y"
