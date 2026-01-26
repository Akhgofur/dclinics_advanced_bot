"""Service for building text messages."""
from typing import List, Dict
from datetime import datetime
from utils.helpers import get_full_name, get_safe_attribute, get_translation
from utils.constants import DateTimeFormats


class TextBuilder:
    """Builder for creating formatted text messages."""
    
    @staticmethod
    def build_services_text(
        data: List[Dict],
        selected_services: List[str]
    ) -> str:
        """Build text representation of services list."""
        content = ""
        
        for index, item in enumerate(data):
            dt = datetime.fromisoformat(get_safe_attribute(item, "registrationDate"))
            date_only = dt.strftime(DateTimeFormats.DISPLAY_DATE_TIME)
            
            checked = "✅" if str(item["id"]) in selected_services else "❌"
            
            content += (
                f"{index + 1}. {checked} {date_only} "
                f"{get_safe_attribute(item, 'admittanceType.title')} - "
                f"{get_full_name(get_safe_attribute(item, 'doctor'))} \n"
            )
        
        return content
    
    @staticmethod
    def build_doctors_text(data: List[Dict]) -> str:
        """Build text representation of doctors list."""
        content = ""
        
        for index, item in enumerate(data):
            content += (
                f"{index + 1}. {get_full_name(item)} "
                f"{get_safe_attribute(item, 'speciality.title')}\n"
            )
        
        return content
    
    @staticmethod
    def build_admittance_type_text(data: List[Dict]) -> str:
        """Build text representation of admittance types list."""
        content = ""
        
        for index, item in enumerate(data):
            amount = float(get_safe_attribute(item, 'amount', 0))
            content += (
                f"{index + 1}. {get_safe_attribute(item, 'title')} - "
                f"<b>{amount}</b>\n"
            )
        
        return content
    
    @staticmethod
    def build_cart_text(data: List[Dict], lang: str = "ru") -> str:
        """Build text representation of cart."""
        if not data:
            return get_translation(lang, "empty_cart")
        
        content = ""
        total_amount_cart = 0
        total_quantity_cart = 0
        
        for index, item in enumerate(data):
            total_quantity_cart += 1
            amount = float(get_safe_attribute(item, 'admittanceType_obj.amount', 0))
            total_amount_cart += amount
            
            doctor_name = get_full_name(get_safe_attribute(item, 'doctor_obj', {}))
            admittance_type = get_safe_attribute(item, 'admittanceType_obj.title')
            registration_date = get_safe_attribute(item, 'registrationDate')
            
            content += (
                f"{index + 1}. <b>{doctor_name}</b> - {admittance_type} "
                f"{registration_date} <b>{amount}</b>\n"
            )
        
        content += f"\n\n<b>{get_translation(lang, 'total_quantity')}: {total_quantity_cart}</b> \n"
        content += f"<b>{get_translation(lang, 'total_amount')}: {total_amount_cart}</b> \n"
        
        return content
