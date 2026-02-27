from fastapi import APIRouter

from src.checkout.dto import CheckoutRequestDTO, OrderDTO
from src.checkout.dependencies.checkout.service import ICheckoutService

router = APIRouter(prefix="/checkout", tags=["Checkout"])

@router.post("/", response_model=OrderDTO, summary="Initiate Checkout Saga")
async def initiate_checkout(
    request: CheckoutRequestDTO,
    checkout_service: ICheckoutService
):
    """
    Submits a checkout request. This triggers the Payment, Inventory, and Shipping steps 
    managed by the Saga Orchestrator. The request can optionally specify `fail_at_step`
    to purposefully simulate a failure and observe the Orchestrator's compensation flow.
    """
    return await checkout_service.process_checkout(request)
