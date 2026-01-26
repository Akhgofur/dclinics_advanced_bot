"""Service for building keyboard layouts."""
from typing import List, Dict, Set, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from utils.helpers import get_translation
from utils.constants import CallbackData, Defaults


class KeyboardBuilder:
    """Builder for creating inline keyboards."""
    
    @staticmethod
    async def build_paginated_keyboard(
        data: List[Dict],
        callback_prefix: str,
        state: FSMContext,
        lang: str = Defaults.LANGUAGE,
        buttons_per_row: int = 5,
        come_back_callback: str = CallbackData.COME_BACK
    ) -> InlineKeyboardMarkup:
        """
        Build a paginated keyboard with numbered buttons.
        
        Args:
            data: List of items to create buttons for
            callback_prefix: Prefix for callback data (e.g., "print_service_")
            state: FSM context
            lang: Language code
            buttons_per_row: Number of buttons per row
            come_back_callback: Callback data for come back button
            
        Returns:
            InlineKeyboardMarkup instance
        """
        buttons = []
        for index, item in enumerate(data):
            button = InlineKeyboardButton(
                text=f"{index + 1}",
                callback_data=f"{callback_prefix}{item['id']}"
            )
            buttons.append(button)
        
        # Group buttons into rows
        rows = [buttons[i:i + buttons_per_row] for i in range(0, len(buttons), buttons_per_row)]
        
        # Add pagination if needed
        state_data = await state.get_data()
        count = state_data.get("count", 0)
        offset = state_data.get("offset", 0)
        limit = state_data.get("limit", Defaults.LIMIT)
        
        paginate_kb = []
        # Extract prefix for pagination (e.g., "doctor" from "admittance_doctor_")
        prefix_parts = callback_prefix.split('_')
        if len(prefix_parts) >= 2:
            pagination_prefix = prefix_parts[-2]  # Get "doctor" from "admittance_doctor_"
        else:
            pagination_prefix = prefix_parts[0]
            
        if offset == 0 and count > limit:
            paginate_kb = [InlineKeyboardButton(text=">", callback_data=f"{pagination_prefix}_next")]
        elif offset > 0 and offset + limit >= count:
            paginate_kb = [InlineKeyboardButton(text="<", callback_data=f"{pagination_prefix}_prev")]
        elif offset > 0:
            paginate_kb = [
                InlineKeyboardButton(text="<", callback_data=f"{pagination_prefix}_prev"),
                InlineKeyboardButton(text=">", callback_data=f"{pagination_prefix}_next")
            ]
        
        if paginate_kb:
            rows.append(paginate_kb)
        
        # Add come back button
        come_back = get_translation(lang, "come_back")
        rows.append([InlineKeyboardButton(text=come_back, callback_data=come_back_callback)])
        
        return InlineKeyboardMarkup(inline_keyboard=rows)
    
    @staticmethod
    async def build_services_keyboard(
        data: List[Dict],
        selected_services: List[str],
        lang: str = Defaults.LANGUAGE
    ) -> InlineKeyboardMarkup:
        """Build keyboard for service selection."""
        buttons = []
        for index, item in enumerate(data):
            button = InlineKeyboardButton(
                text=f"{index + 1}",
                callback_data=f"{CallbackData.PRINT_SERVICE_PREFIX}{item['id']}"
            )
            buttons.append(button)
        
        rows = [buttons[i:i + 5] for i in range(0, len(buttons), 5)]
        
        come_back = get_translation(lang, "come_back")
        print_results = get_translation(lang, "print_results")
        
        if len(selected_services) == 0:
            rows.append([InlineKeyboardButton(text=come_back, callback_data=CallbackData.COME_BACK)])
        else:
            rows.append([
                InlineKeyboardButton(text=come_back, callback_data=CallbackData.COME_BACK),
                InlineKeyboardButton(text=print_results, callback_data=CallbackData.PRINT_RESULTS)
            ])
        
        return InlineKeyboardMarkup(inline_keyboard=rows)
    
    @staticmethod
    def build_hour_buttons(
        start_hour: int,
        end_hour: int,
        blocked_times: Set[str]
    ) -> InlineKeyboardMarkup:
        """
        Build time slot buttons, skipping blocked times.
        
        Args:
            start_hour: Starting hour (0-23)
            end_hour: Ending hour (0-23)
            blocked_times: Set of blocked time strings (HH:MM format)
            
        Returns:
            InlineKeyboardMarkup with time buttons
        """
        if not (0 <= start_hour <= 23 and 0 <= end_hour <= 23 and start_hour <= end_hour):
            raise ValueError("start_hour and end_hour must be in range 0–23 and start <= end")
        
        inline_keyboard = []
        
        for hour in range(start_hour, end_hour + 1):
            row = []
            for minute in ["00", "30"]:
                time_str = f"{hour:02d}:{minute}"
                if time_str not in blocked_times:
                    row.append(
                        InlineKeyboardButton(
                            text=time_str,
                            callback_data=f"{CallbackData.SELECT_HOUR_PREFIX}{time_str}"
                        )
                    )
            
            if row:
                inline_keyboard.append(row)
        
        return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
