"""User handlers module."""
from . import help
from . import start_refactored as start
from . import callback_handlers

# Combine all routers
from aiogram import Router

router = Router()

# Include main routers
router.include_router(start.router)
router.include_router(callback_handlers.router)
