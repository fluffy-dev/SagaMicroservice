import pytest
from unittest.mock import AsyncMock
from src.libs.saga import ISagaStep, SagaOrchestrator, SagaExecutionError
from typing import List


class DummyContext:
    def __init__(self, failure_point: str = None):
        self.failure_point = failure_point
        self.execution_order = []
        self.compensation_order = []


class MockStep(ISagaStep[DummyContext]):
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    async def execute(self, context: DummyContext) -> None:
        context.execution_order.append(self.name)
        if context.failure_point == self.name:
            raise ValueError(f"Failing at {self.name} on purpose")

    async def compensate(self, context: DummyContext) -> None:
        context.compensation_order.append(self.name)


@pytest.mark.asyncio
async def test_saga_orchestrator_success():
    context = DummyContext()
    orchestrator = SagaOrchestrator([
        MockStep("Step1"),
        MockStep("Step2"),
        MockStep("Step3"),
    ])

    await orchestrator.execute(context)

    assert context.execution_order == ["Step1", "Step2", "Step3"]
    assert context.compensation_order == []


@pytest.mark.asyncio
async def test_saga_orchestrator_failure_compensates_in_reverse():
    context = DummyContext(failure_point="Step3")
    orchestrator = SagaOrchestrator([
        MockStep("Step1"),
        MockStep("Step2"),
        MockStep("Step3"),
    ])

    with pytest.raises(SagaExecutionError) as exc_info:
        await orchestrator.execute(context)

    assert exc_info.value.step_name == "Step3"
    assert "Failing at Step3 on purpose" in str(exc_info.value.original_exception)

    assert context.execution_order == ["Step1", "Step2", "Step3"]

    assert context.compensation_order == ["Step2", "Step1"]


@pytest.mark.asyncio
async def test_saga_orchestrator_emits_events_when_publisher_provided():
    """Verifies that lifecycle events are emitted for each step when a publisher is configured."""
    context = DummyContext()
    mock_publisher = AsyncMock()
    mock_publisher.publish = AsyncMock()

    orchestrator = SagaOrchestrator(
        steps=[MockStep("Step1"), MockStep("Step2")],
        event_publisher=mock_publisher,
        event_topic="saga.events.test",
    )

    await orchestrator.execute(context)

    assert mock_publisher.publish.await_count == 4
    call_args_list = [
        call.kwargs["value"]["event_type"]
        for call in mock_publisher.publish.call_args_list
    ]
    assert call_args_list == [
        "saga.step.started",
        "saga.step.completed",
        "saga.step.started",
        "saga.step.completed",
    ]


@pytest.mark.asyncio
async def test_saga_orchestrator_emits_failure_event():
    """Verifies that a failure event is emitted when a step fails."""
    context = DummyContext(failure_point="Step2")
    mock_publisher = AsyncMock()
    mock_publisher.publish = AsyncMock()

    orchestrator = SagaOrchestrator(
        steps=[MockStep("Step1"), MockStep("Step2")],
        event_publisher=mock_publisher,
        event_topic="saga.events.test",
    )

    with pytest.raises(SagaExecutionError):
        await orchestrator.execute(context)

    event_types = [
        call.kwargs["value"]["event_type"]
        for call in mock_publisher.publish.call_args_list
    ]
    assert "saga.step.failed" in event_types
    assert "saga.compensation.started" in event_types


@pytest.mark.asyncio
async def test_saga_orchestrator_works_without_publisher():
    """Verifies backward compatibility: orchestrator works fine without a publisher."""
    context = DummyContext()
    orchestrator = SagaOrchestrator(
        steps=[MockStep("Step1"), MockStep("Step2")],
    )

    await orchestrator.execute(context)

    assert context.execution_order == ["Step1", "Step2"]
