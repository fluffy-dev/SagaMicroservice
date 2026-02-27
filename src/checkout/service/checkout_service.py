import logging
from src.checkout.dto import CheckoutRequestDTO, CreateOrderDTO, OrderDTO, UpdateOrderDTO
from src.checkout.models.order import OrderStatus
from src.checkout.entities import SagaContext
from src.checkout.dependencies.order.repository import IOrderRepository
from src.libs.saga import SagaOrchestrator, SagaExecutionError
from src.checkout.service.steps import PaymentStep, InventoryStep, ShippingStep

logger = logging.getLogger(__name__)

class CheckoutService:
    """Service layer coordinating checkout operations using the Saga Pattern."""

    def __init__(self, order_repo: IOrderRepository):
        """Initializes the CheckoutService.

        Args:
            order_repo: The repository handling order persistence.
        """
        self.order_repo = order_repo
        
    async def process_checkout(self, request: CheckoutRequestDTO) -> OrderDTO:
        """Processes a checkout request dynamically injecting steps.

        Args:
            request: The checkout details including items and user identifiers.

        Returns:
            OrderDTO: The processed order representation.

        Raises:
            Exception: If an unhandled failure occurs during checkout orchestration.
        """
        order_dto = await self.order_repo.create(CreateOrderDTO(
            user_id=request.user_id,
            item_id=request.item_id,
            quantity=request.quantity,
            price=request.price
        ))
        
        context = SagaContext(
            order_id=order_dto.id,
            user_id=request.user_id,
            item_id=request.item_id,
            quantity=request.quantity,
            price=request.price,
            fail_at_step=request.fail_at_step
        )
        
        orchestrator = SagaOrchestrator[SagaContext](steps=[
            PaymentStep(),
            InventoryStep(),
            ShippingStep()
        ])
        
        try:
            logger.info(f"Starting checkout Saga for order {order_dto.id}")
            await orchestrator.execute(context)
            
            logger.info(f"Saga completed successfully for order {order_dto.id}.")
            final_order = await self.order_repo.update(
                UpdateOrderDTO(status=OrderStatus.COMPLETED), pk=order_dto.id
            )
            return final_order
            
        except SagaExecutionError as e:
            logger.error(f"Saga failed during checkout for order {order_dto.id}.")
            final_order = await self.order_repo.update(
                UpdateOrderDTO(status=OrderStatus.FAILED), pk=order_dto.id
            )
            return final_order
        
        except Exception as e:
            logger.critical(f"Unexpected error in CheckoutService: {e}")
            raise e
