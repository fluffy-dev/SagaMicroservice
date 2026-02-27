from fastapi import Depends
from typing import Annotated

from src.checkout.service.checkout_service import CheckoutService

ICheckoutService = Annotated[CheckoutService, Depends()]
