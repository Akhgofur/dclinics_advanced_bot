import logging
from aiogram import Router
from aiogram.types import Update
from aiogram.exceptions import (
    TelegramUnauthorizedError,
    TelegramBadRequest,
    TelegramAPIError,
    TelegramRetryAfter,
    TelegramNetworkError,
)

router = Router()

@router.errors()
async def global_error_handler(update: Update, exception: Exception):
    """
    Global error handler for Aiogram 3.x.
    """

    if isinstance(exception, TelegramUnauthorizedError):
        logging.exception(f"Unauthorized: {exception}")
        return True

    if isinstance(exception, TelegramBadRequest):
        logging.exception(f"BadRequest: {exception} \nUpdate: {update}")
        return True

    if isinstance(exception, TelegramRetryAfter):
        logging.exception(f"RetryAfter: {exception} \nUpdate: {update}")
        return True

    if isinstance(exception, TelegramAPIError):
        logging.exception(f"TelegramAPIError: {exception} \nUpdate: {update}")
        return True

    if isinstance(exception, TelegramNetworkError):
        logging.exception(f"Network error: {exception} \nUpdate: {update}")
        return True

    # Catch-all for other unhandled exceptions
    logging.exception(f"Unhandled error\nUpdate: {update}\nException: {exception}")
    return True
