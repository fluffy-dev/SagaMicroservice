import logging
from datetime import datetime, timezone
from typing import List, Generic, TypeVar, Optional

from src.libs.saga.interfaces import ISagaStep
from src.libs.saga.exceptions import SagaExecutionError, SagaCompensationError
from src.libs.event_bus.interfaces import IEventPublisher

TContext = TypeVar("TContext")

logger = logging.getLogger(__name__)


class SagaOrchestrator(Generic[TContext]):
    """Orchestrates the execution of multiple ISagaSteps.

    If any step's ``execute`` method fails, it will execute the ``compensate``
    method of all previously successfully executed steps in reverse order.

    Optionally emits structured lifecycle events to an event publisher.
    """

    def __init__(
        self,
        steps: List[ISagaStep[TContext]],
        event_publisher: Optional[IEventPublisher] = None,
        event_topic: Optional[str] = None,
    ) -> None:
        """Initializes the orchestrator with steps and optional event publisher.

        Args:
            steps: Ordered list of saga steps to execute.
            event_publisher: Optional publisher for saga lifecycle events.
            event_topic: The topic to publish lifecycle events to.
        """
        self.steps = steps
        self._event_publisher = event_publisher
        self._event_topic = event_topic

    async def execute(self, context: TContext) -> None:
        """Executes the saga sequentially.

        If an execution fails, it triggers the compensation flow. When an event
        publisher is configured, lifecycle events are emitted for each step.

        Args:
            context: The shared context object passed through all steps.

        Raises:
            SagaExecutionError: If any step fails during execution.
        """
        executed_steps: List[ISagaStep[TContext]] = []

        logger.info(f"Starting Saga Execution over {len(self.steps)} steps.")

        for step in self.steps:
            try:
                logger.debug(f">> Executing saga step: {step.name}")
                await self._emit_event("saga.step.started", step.name)
                await step.execute(context)
                executed_steps.append(step)
                await self._emit_event("saga.step.completed", step.name)
                logger.debug(f"<< Successfully executed saga step: {step.name}")

            except Exception as e:
                logger.error(
                    f"!! Failed saga step: {step.name}, error: {e}. "
                    f"Initiating compensation."
                )
                await self._emit_event("saga.step.failed", step.name, error=str(e))
                await self._compensate(executed_steps, context)

                raise SagaExecutionError(
                    step_name=step.name, original_exception=e
                ) from e

        logger.info("Saga Execution completed successfully.")

    async def _compensate(
        self,
        executed_steps: List[ISagaStep[TContext]],
        context: TContext,
    ) -> None:
        """Reverses the executed steps and calls their compensate methods.

        Args:
            executed_steps: Steps that completed successfully before the failure.
            context: The shared context object.

        Raises:
            SagaCompensationError: If any compensation step fails.
        """
        for step in reversed(executed_steps):
            try:
                logger.warning(f"<< Compensating saga step: {step.name}")
                await self._emit_event("saga.compensation.started", step.name)
                await step.compensate(context)
                logger.warning(f">> Successfully compensated saga step: {step.name}")
            except Exception as e:
                logger.critical(
                    f"!! CRITICAL: Failed to compensate saga step: "
                    f"{step.name}, error: {e}"
                )
                raise SagaCompensationError(
                    step_name=step.name, original_exception=e
                ) from e

    async def _emit_event(
        self,
        event_type: str,
        step_name: str,
        error: str = "",
    ) -> None:
        """Publishes a saga lifecycle event if a publisher is configured.

        Args:
            event_type: The type identifier for the lifecycle event.
            step_name: The name of the saga step this event relates to.
            error: Optional error message if the event represents a failure.
        """
        if not self._event_publisher or not self._event_topic:
            return

        event = {
            "event_type": event_type,
            "step_name": step_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": error,
        }
        try:
            await self._event_publisher.publish(
                topic=self._event_topic,
                key=step_name,
                value=event,
            )
        except Exception as e:
            logger.warning(f"Failed to emit saga event: {e}")
