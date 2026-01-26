"""Helper functions for FSM state management."""
from typing import Dict, Any, Optional
from aiogram.fsm.context import FSMContext
from utils.constants import Defaults


class StateData:
    """Helper class for accessing state data with common defaults."""
    
    def __init__(self, state_data: Dict[str, Any]):
        self._data = state_data
    
    @property
    def language(self) -> str:
        """Get language from state, defaulting to 'ru'."""
        return self._data.get("language", Defaults.LANGUAGE)
    
    @property
    def patient_id(self) -> Optional[int]:
        """Get patient ID from state."""
        return self._data.get("patient_id")
    
    @property
    def patient_guid(self) -> Optional[str]:
        """Get patient GUID from state."""
        return self._data.get("patient_guid")
    
    @property
    def step(self) -> str:
        """Get current step from state."""
        return self._data.get("step", "")
    
    @property
    def add_patient(self) -> bool:
        """Get add_patient flag from state."""
        return self._data.get("add_patient", False)
    
    @property
    def phone_number(self) -> str:
        """Get phone number from state."""
        return self._data.get("phone_number", "")
    
    @property
    def cart(self) -> list:
        """Get cart from state."""
        return self._data.get("cart", [])
    
    @property
    def service(self) -> dict:
        """Get service from state."""
        return self._data.get("service", {})
    
    @property
    def patient_form(self) -> dict:
        """Get patient form from state."""
        return self._data.get("patient_form", {})
    
    @property
    def selected_services_print(self) -> list:
        """Get selected services for printing."""
        return self._data.get("selected_services_print", [])
    
    @property
    def fetched_services(self) -> list:
        """Get fetched services."""
        return self._data.get("fetched_services", [])
    
    @property
    def fetched_doctors(self) -> list:
        """Get fetched doctors."""
        return self._data.get("fetched_doctors", [])
    
    @property
    def fetched_admittance_type(self) -> list:
        """Get fetched admittance types."""
        return self._data.get("fetched_admittanceType", [])
    
    @property
    def limit(self) -> int:
        """Get pagination limit."""
        return self._data.get("limit", Defaults.LIMIT)
    
    @property
    def offset(self) -> int:
        """Get pagination offset."""
        return self._data.get("offset", Defaults.OFFSET)
    
    @property
    def count(self) -> int:
        """Get pagination count."""
        return self._data.get("count", Defaults.COUNT)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from state data."""
        return self._data.get(key, default)


async def get_state_data(state: FSMContext) -> StateData:
    """
    Get state data as a StateData helper object.
    
    Usage:
        state_data = await get_state_data(state)
        lang = state_data.language
        patient_id = state_data.patient_id
    """
    data = await state.get_data()
    return StateData(data)
