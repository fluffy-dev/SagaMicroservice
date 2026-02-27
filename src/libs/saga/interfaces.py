from typing import Protocol, TypeVar, Generic, Any

# Define a generic Context type to allow type hinting if desired
TContext = TypeVar("TContext", contravariant=True)

class ISagaStep(Protocol[TContext]):
    """
    Protocol defining the required methods for a single step within a Saga.
    """
    
    @property
    def name(self) -> str:
        """The identifier name of this saga step for logging/debugging."""
        ...

    async def execute(self, context: TContext) -> None:
        """
        Executes the main logic of the saga step.
        If an exception is raised, it indicates that the step failed.
        """
        ...
    
    async def compensate(self, context: TContext) -> None:
        """
        Executes the compensation logic designed to undo the effect of `execute`.
        This is called sequentially in reverse order if a subsequent step fails.
        """
        ...
