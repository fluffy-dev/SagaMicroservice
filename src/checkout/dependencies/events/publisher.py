from typing import Annotated

from fastapi import Depends, Request

from src.libs.event_bus.interfaces import IEventPublisher


def get_event_publisher(request: Request) -> IEventPublisher:
    """Extracts the event publisher from the application state.

    Args:
        request: The incoming FastAPI request.

    Returns:
        The shared IEventPublisher instance.
    """
    return request.app.state.event_publisher


IEventPublisherDep = Annotated[IEventPublisher, Depends(get_event_publisher)]
