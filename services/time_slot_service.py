"""Service for handling time slot calculations."""
from typing import List, Dict, Set
from datetime import datetime, timedelta


class TimeSlotService:
    """Service for calculating available time slots."""
    
    @staticmethod
    def _slot_label(dt: datetime) -> str:
        """Convert datetime to time slot label (HH:00 or HH:30)."""
        return f"{dt.hour:02d}:{'00' if dt.minute < 30 else '30'}"
    
    @staticmethod
    def _overlapping_slots(start: datetime, end: datetime) -> Set[str]:
        """
        Calculate all half-hour slots that overlap with a time range.
        
        Args:
            start: Start datetime
            end: End datetime
            
        Returns:
            Set of time slot labels (HH:MM format)
        """
        # Start at the floor to :00 or :30
        minute = 0 if start.minute < 30 else 30
        slot = start.replace(minute=minute, second=0, microsecond=0)
        if slot > start:
            slot -= timedelta(minutes=30)
        
        out = set()
        while slot < end:
            slot_end = slot + timedelta(minutes=30)
            # Any intersection with [start, end)
            if slot_end > start and slot < end:
                out.add(f"{slot.hour:02d}:{'00' if slot.minute == 0 else '30'}")
            slot += timedelta(minutes=30)
        
        return out
    
    @staticmethod
    def get_blocked_half_hour_slots(
        reserves: List[Dict],
        services: List[Dict]
    ) -> Set[str]:
        """
        Get all blocked time slots from reserves and services.
        
        Args:
            reserves: List of reserve periods with 'start' and 'end' keys
            services: List of services with 'registrationDate' key
            
        Returns:
            Set of blocked time slot labels (HH:MM format)
        """
        blocked: Set[str] = set()
        
        # Block service registration half-hour slots
        for service in services:
            reg_date = service.get("registrationDate")
            if reg_date:
                try:
                    dt = datetime.fromisoformat(reg_date)
                    blocked.add(TimeSlotService._slot_label(dt))
                except Exception:
                    pass
        
        # Block every half-hour that overlaps reserve periods
        for reserve in reserves:
            start, end = reserve.get("start"), reserve.get("end")
            if start and end:
                try:
                    dt_start = datetime.fromisoformat(start)
                    dt_end = datetime.fromisoformat(end)
                    if dt_end > dt_start:
                        blocked |= TimeSlotService._overlapping_slots(dt_start, dt_end)
                except Exception:
                    pass
        
        return blocked
