"""Helper functions for keyboard operations."""
from aiogram.fsm.context import FSMContext
from keyboards.default.main import get_main_keyboard as _get_main_keyboard


async def get_main_keyboard(state: FSMContext):
    """
    Get main menu keyboard.
    
    Centralized function to avoid duplication across handlers.
    """
    return await _get_main_keyboard(state)
