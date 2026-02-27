class SagaExecutionError(Exception):
    """
    Exception raised when a Saga fails during the `execute` phase.
    It wraps the original exception and contains the name of the failing step.
    """
    def __init__(self, step_name: str, original_exception: Exception):
        self.step_name = step_name
        self.original_exception = original_exception
        super().__init__(f"Saga step '{step_name}' failed during execution: {original_exception}")


class SagaCompensationError(Exception):
    """
    Exception raised when a Saga fails during the `compensate` phase.
    This implies a critical failure during rollback that may require manual intervention.
    """
    def __init__(self, step_name: str, original_exception: Exception):
        self.step_name = step_name
        self.original_exception = original_exception
        super().__init__(f"CRITICAL: Saga compensation step '{step_name}' failed: {original_exception}")
