import logging
from src.libs.saga import ISagaStep
from src.checkout.entities import SagaContext

logger = logging.getLogger(__name__)

class PaymentStep(ISagaStep[SagaContext]):
    @property
    def name(self) -> str:
        return "PaymentStep"

    async def execute(self, context: SagaContext) -> None:
        logger.info(f"[{self.name}] Initiating payment for order {context.order_id}, amount: {context.price}")
        if context.fail_at_step == self.name:
            raise ValueError(f"Simulated failure at {self.name}!")
        logger.info(f"[{self.name}] Payment successful.")

    async def compensate(self, context: SagaContext) -> None:
        logger.warning(f"[{self.name}] Refund initiated for order {context.order_id}, amount: {context.price}")
        logger.warning(f"[{self.name}] Refund completed.")


class InventoryStep(ISagaStep[SagaContext]):
    @property
    def name(self) -> str:
        return "InventoryStep"

    async def execute(self, context: SagaContext) -> None:
        logger.info(f"[{self.name}] Reserving {context.quantity} units of {context.item_id} for order {context.order_id}")
        if context.fail_at_step == self.name:
            raise ValueError(f"Simulated failure at {self.name}! Insufficient stock.")
        logger.info(f"[{self.name}] Stock reserved successfully.")

    async def compensate(self, context: SagaContext) -> None:
        logger.warning(f"[{self.name}] Releasing {context.quantity} units of reserved stock for {context.item_id}")
        logger.warning(f"[{self.name}] Stock released.")


class ShippingStep(ISagaStep[SagaContext]):
    @property
    def name(self) -> str:
        return "ShippingStep"

    async def execute(self, context: SagaContext) -> None:
        logger.info(f"[{self.name}] Booking shipment for order {context.order_id}")
        if context.fail_at_step == self.name:
            raise ValueError(f"Simulated failure at {self.name}! Courier API unreachable.")
        logger.info(f"[{self.name}] Shipment booked successfully.")

    async def compensate(self, context: SagaContext) -> None:
        logger.warning(f"[{self.name}] Cancelling shipment booking for order {context.order_id}")
        logger.warning(f"[{self.name}] Shipment cancelled.")
