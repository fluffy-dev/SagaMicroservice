from dataclasses import dataclass
from src.checkout.models.order import OrderStatus

@dataclass
class OrderEntity:
    user_id: int
    item_id: str
    quantity: int
    price: int
    status: OrderStatus = OrderStatus.PENDING

@dataclass
class SagaContext:
    """
    Context passed down through Saga Orchestrator steps.
    Used for simulating state, transferring variables, and conditionally failing.
    """
    order_id: int
    user_id: int
    item_id: str
    quantity: int
    price: int
    fail_at_step: str | None = None
