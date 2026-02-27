from pydantic import BaseModel
from typing import Optional
from src.checkout.models.order import OrderStatus

class BaseOrderDTO(BaseModel):
    id: Optional[int] = None
    user_id: int
    item_id: str
    quantity: int
    price: int
    status: OrderStatus

class CreateOrderDTO(BaseModel):
    user_id: int
    item_id: str
    quantity: int
    price: int

class UpdateOrderDTO(BaseModel):
    status: OrderStatus

class OrderDTO(BaseOrderDTO):
    """Returned from methods looking up an order."""
    pass

class CheckoutRequestDTO(BaseModel):
    user_id: int
    item_id: str
    quantity: int
    price: int
    # For testing saga failure
    fail_at_step: Optional[str] = None
