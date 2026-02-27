"""
This module defines the main project endpoints
"""

from typing import Callable

from fastapi import APIRouter
from src.auth.router import router as auth_router
from src.checkout.router import router as checkout_router

router = APIRouter(prefix="/v1", tags=["v1"])

# register here apps routers

router.include_router(auth_router)
router.include_router(checkout_router)

