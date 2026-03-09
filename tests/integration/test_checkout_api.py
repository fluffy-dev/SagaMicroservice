import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.checkout.models.order import OrderModel, OrderStatus

@pytest.mark.asyncio
async def test_checkout_saga_success(client: AsyncClient, db_session: AsyncSession):
    payload = {
        "user_id": 1,
        "item_id": "SKU-1234",
        "quantity": 2,
        "price": 5000 # 50.00
    }
    
    response = await client.post("/v1/checkout/", json=payload)
    
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert "id" in data
    
    # Verify DB State
    order_id = data["id"]
    db_result = await db_session.execute(select(OrderModel).where(OrderModel.id == order_id))
    order = db_result.scalar_one()
    assert order.status == OrderStatus.COMPLETED


@pytest.mark.asyncio
async def test_checkout_saga_failure_at_shipping(client: AsyncClient, db_session: AsyncSession):
    payload = {
        "user_id": 1,
        "item_id": "SKU-1234",
        "quantity": 2,
        "price": 5000,
        "fail_at_step": "ShippingStep"
    }
    
    response = await client.post("/v1/checkout/", json=payload)
    
    # In our implementation, we catch the SagaExecutionError and return 
    # the failed order record (status 200 with FAILED status) and rollback the REST of the transaction
    # (though actually the record is marked failed explicitly over the session).
    
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "FAILED"
    
    # Verify DB State
    order_id = data["id"]
    db_result = await db_session.execute(select(OrderModel).where(OrderModel.id == order_id))
    order = db_result.scalar_one()
    assert order.status == OrderStatus.FAILED
