from fastapi import Depends
from typing import Annotated

from src.checkout.repositories.order import OrderRepository

IOrderRepository: type[OrderRepository] = Annotated[OrderRepository, Depends()]
