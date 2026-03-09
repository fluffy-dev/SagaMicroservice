from fastapi import APIRouter

from src.checkout.dto import CheckoutRequestDTO, OrderDTO
from src.checkout.dependencies.checkout.service import ICheckoutService

router = APIRouter(prefix="/checkout", tags=["Checkout"])


@router.post("/", response_model=OrderDTO, summary="Initiate Checkout Saga")
async def initiate_checkout(
    request: CheckoutRequestDTO,
    checkout_service: ICheckoutService,
) -> OrderDTO:
    """Submits a checkout request triggering the Payment, Inventory, and Shipping
    steps managed by the Saga Orchestrator.

    The request can optionally specify ``fail_at_step`` to simulate a failure
    and observe the Orchestrator's compensation flow.

    Duplicate requests within the idempotency TTL window return the cached result.
    """
    return await checkout_service.process_checkout(request)


@router.get(
    "/{order_id}",
    response_model=OrderDTO,
    summary="Get Order Status",
)
async def get_order(
    order_id: int,
    checkout_service: ICheckoutService,
) -> OrderDTO:
    """Retrieves an order by its ID, serving from Redis cache when available.

    Falls back to the database on cache miss and populates the cache for
    subsequent requests.
    """
    order = await checkout_service.get_order(order_id)
    if order is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Order not found")
    return order
