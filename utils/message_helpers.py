"""Helper functions for message handling."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from utils.helpers import get_translation
from utils.state_helpers import get_state_data


@asynccontextmanager
async def loading_message(
    message: Message,
    state: FSMContext,
    loading_text_key: str = "loading"
) -> AsyncGenerator[Message, None]:
    """
    Context manager for showing and automatically deleting loading messages.
    
    Usage:
        async with loading_message(message, state) as loading_msg:
            # Do async work
            result = await some_async_operation()
    """
    state_data = await get_state_data(state)
    lang = state_data.language
    
    loading_msg = await message.answer(get_translation(lang, loading_text_key))
    
    try:
        yield loading_msg
    finally:
        await loading_msg.delete()


async def get_language(state: FSMContext) -> str:
    """Get language from state with default."""
    state_data = await get_state_data(state)
    return state_data.language


async def send_error_message(
    message: Message,
    state: FSMContext,
    error_key: str = "try_again"
) -> None:
    """Send error message using translation."""
    lang = await get_language(state)
    await message.answer(get_translation(lang, error_key))
