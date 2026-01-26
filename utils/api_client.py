"""Centralized API client for backend communication."""
import ssl
import asyncio
import aiohttp
from typing import Optional, Dict, List, Any
from environs import Env

env = Env()
env.read_env()
BACK_END_URL = env.str("BACK_END_URL")

# Constants
REQUEST_TIMEOUT = 10
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE


class APIClient:
    """Centralized API client for making HTTP requests to the backend."""
    
    def __init__(self, base_url: str = BACK_END_URL, timeout: int = REQUEST_TIMEOUT):
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.ssl_context = SSL_CONTEXT
    
    async def get(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        Make a GET request to the API.
        
        Args:
            endpoint: API endpoint (e.g., '/api/patient/')
            params: Query parameters
            
        Returns:
            Response data or None if request failed
        """
        url = f"{self.base_url}{endpoint}"
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, ssl=self.ssl_context, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return None
    
    async def post(
        self, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        Make a POST request to the API.
        
        Args:
            endpoint: API endpoint
            data: Form data
            json_data: JSON data
            
        Returns:
            Response data or None if request failed
        """
        url = f"{self.base_url}{endpoint}"
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    url, 
                    ssl=self.ssl_context, 
                    data=data,
                    json=json_data
                ) as response:
                    if response.status in [200, 201, 204]:
                        return await response.json()
                    return None
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return None
    
    async def get_patient_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """Get patient by phone number."""
        data = await self.get(f"/api/patient/?q={phone}")
        return data[0] if data and len(data) > 0 else None
    
    async def get_services_by_patient(
        self, 
        patient_id: int, 
        ordering: str = "-registrationDate",
        is_confirmed: bool = True
    ) -> Optional[List[Dict[str, Any]]]:
        """Get services for a patient."""
        params = {
            "patient": patient_id,
            "ordering": ordering,
            "isConfirmed": is_confirmed
        }
        return await self.get("/api/admittance-service/", params=params)
    
    async def get_doctors(
        self, 
        role: int = 2, 
        limit: int = 10, 
        offset: int = 0
    ) -> Optional[Dict[str, Any]]:
        """Get list of doctors."""
        params = {
            "role": role,
            "p": "true",
            "limit": limit,
            "offset": offset
        }
        return await self.get("/api/staff/", params=params)
    
    async def get_admittance_types(
        self, 
        doctor_id: int,
        limit: int = 10, 
        offset: int = 0
    ) -> Optional[Dict[str, Any]]:
        """Get admittance types for a doctor."""
        params = {
            "p": "true",
            "limit": limit,
            "offset": offset,
            "user": doctor_id,
            "showBot": "true"
        }
        return await self.get("/api/admittance-type/", params=params)
    
    async def get_doctor_timetable(
        self, 
        doctor_id: int, 
        date: str, 
        is_confirmed: bool = True
    ) -> Optional[List[Dict[str, Any]]]:
        """Get doctor timetable for a specific date."""
        params = {
            "doctor": doctor_id,
            "date": date,
            "isConfirmed": is_confirmed
        }
        data = await self.get("/api/doctor-timetable/", params=params)
        return data[0] if data and len(data) > 0 else None
    
    async def create_patient(self, patient_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new patient."""
        return await self.post("/api/patient/", data=patient_data)
    
    async def create_admittance(self, admittance_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new admittance."""
        return await self.post("/api/admittance/", json_data=admittance_data)
    
    async def get_admittance_by_code(self, code: str) -> Optional[List[Dict[str, Any]]]:
        """Get admittance by code."""
        return await self.get(f"/api/admittance/?q={code}")
    
    async def get_chosen_services(self, service_ids: str) -> Optional[List[Dict[str, Any]]]:
        """Get chosen services by IDs."""
        return await self.get(f"/api/admittance-service/chosen?id={service_ids}")


# Global instance
api_client = APIClient()
