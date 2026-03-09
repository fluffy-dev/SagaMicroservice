from datetime import datetime, timezone

from pydantic import BaseModel


class CheckoutEvent(BaseModel):
    """Base schema for all checkout domain events."""

    event_type: str
    order_id: int
    user_id: int
    item_id: str
    quantity: int
    price: int
    timestamp: str


class CheckoutCompletedEvent(CheckoutEvent):
    """Event emitted when a checkout saga completes successfully."""

    event_type: str = "checkout.completed"


class CheckoutFailedEvent(CheckoutEvent):
    """Event emitted when a checkout saga fails and compensation is triggered."""

    event_type: str = "checkout.failed"
    failed_at_step: str = ""


def build_checkout_event(
    event_cls: type[CheckoutEvent],
    order_id: int,
    user_id: int,
    item_id: str,
    quantity: int,
    price: int,
    **kwargs,
) -> dict:
    """Constructs a serializable checkout event dictionary.

    Args:
        event_cls: The Pydantic event class to instantiate.
        order_id: The order identifier.
        user_id: The user who initiated checkout.
        item_id: The purchased item identifier.
        quantity: The number of units.
        price: The total price in cents.
        **kwargs: Additional fields specific to the event subclass.

    Returns:
        A dictionary representation of the event ready for publishing.
    """
    event = event_cls(
        order_id=order_id,
        user_id=user_id,
        item_id=item_id,
        quantity=quantity,
        price=price,
        timestamp=datetime.now(timezone.utc).isoformat(),
        **kwargs,
    )
    return event.model_dump()
