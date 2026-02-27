from typing import List, Generic, TypeVar
import logging

from src.libs.saga.interfaces import ISagaStep
from src.libs.saga.exceptions import SagaExecutionError, SagaCompensationError

# Reuse the defined generic TContext
TContext = TypeVar("TContext")

logger = logging.getLogger(__name__)

class SagaOrchestrator(Generic[TContext]):
    """
    Orchestrates the execution of multiple ISagaSteps.
    If any step's `execute` method fails (throws), it will execute the `compensate` 
    method of all previously successfully executed steps in reverse order.
    """

    def __init__(self, steps: List[ISagaStep[TContext]]):
        self.steps = steps
        
    async def execute(self, context: TContext) -> None:
        """
        Executes the saga sequentially.
        If an execution fails, it triggers the compensation flow.
        """
        executed_steps: List[ISagaStep[TContext]] = []
        
        logger.info(f"Starting Saga Execution over {len(self.steps)} steps.")

        for step in self.steps:
            try:
                logger.debug(f">> Executing saga step: {step.name}")
                await step.execute(context)
                executed_steps.append(step)
                logger.debug(f"<< Successfully executed saga step: {step.name}")
                
            except Exception as e:
                logger.error(f"!! Failed saga step: {step.name}, error: {e}. Initiating compensation.")
                # Halt execution and start compensation
                await self._compensate(executed_steps, context)
                
                # Finally, re-raise as SagaExecutionError to inform the caller
                raise SagaExecutionError(step_name=step.name, original_exception=e) from e

        logger.info("Saga Execution completed successfully.")

    async def _compensate(self, executed_steps: List[ISagaStep[TContext]], context: TContext) -> None:
        """
        Reverses the executed steps and calls their `compensate` methods.
        """
        # Iterate in reverse order
        for step in reversed(executed_steps):
            try:
                logger.warning(f"<< Compensating saga step: {step.name}")
                await step.compensate(context)
                logger.warning(f">> Successfully compensated saga step: {step.name}")
            except Exception as e:
                logger.critical(f"!! CRITICAL: Failed to compensate saga step: {step.name}, error: {e}")
                # For this simple reference implementation, we wrap and re-raise.
                # In robust production environments, you might queue this for retry 
                # or log it loudly to be resolved manually by ops.
                raise SagaCompensationError(step_name=step.name, original_exception=e) from e
