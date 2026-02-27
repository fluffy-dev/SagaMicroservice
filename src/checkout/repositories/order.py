from typing import Optional

from sqlalchemy import select, update
from src.config.database.session import ISession
from src.checkout.models.order import OrderModel, OrderStatus
from src.checkout.dto import CreateOrderDTO, OrderDTO, UpdateOrderDTO

class OrderRepository:
    """
    Repository for handling Order database operations using SQLAlchemy.
    """
    def __init__(self, session: ISession) -> None:
        self.session: ISession = session

    async def create(self, dto: CreateOrderDTO) -> OrderDTO:
        """Creates a new pending order.

        Args:
            dto: CreateOrderDTO object containing order details.

        Returns:
            OrderDTO: The created order Data Transfer Object.
        """
        instance = OrderModel(
            user_id=dto.user_id,
            item_id=dto.item_id,
            quantity=dto.quantity,
            price=dto.price,
            status=OrderStatus.PENDING
        )
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return self._get_dto(instance)

    async def get(self, pk: int) -> Optional[OrderDTO]:
        instance = await self.session.get(OrderModel, pk)
        return self._get_dto(instance) if instance else None

    async def update(self, dto: UpdateOrderDTO, pk: int) -> OrderDTO:
        """Updates an existing order.

        Args:
            dto: UpdateOrderDTO carrying fields to perform an update.
            pk: Integer primary key for the target Order.

        Returns:
            OrderDTO: Updated object representation.
            
        Raises:
            ValueError: If an order with the specific primary key is not found.
        """
        stmt = (
            update(OrderModel)
            .values(**dto.model_dump(exclude_none=True))
            .where(OrderModel.id == pk)
            .returning(OrderModel)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        instance = result.scalar_one_or_none()
        if instance is None:
            raise ValueError(f"Order with id {pk} not found")
        return self._get_dto(instance)

    @staticmethod
    def _get_dto(instance: OrderModel) -> OrderDTO:
        return OrderDTO(
            id=instance.id,
            user_id=instance.user_id,
            item_id=instance.item_id,
            quantity=instance.quantity,
            price=instance.price,
            status=instance.status,
        )
