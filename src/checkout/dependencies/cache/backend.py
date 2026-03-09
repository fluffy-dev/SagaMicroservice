from typing import Annotated

from fastapi import Depends, Request

from src.libs.cache.interfaces import ICacheBackend


def get_cache_backend(request: Request) -> ICacheBackend:
    """Extracts the cache backend from the application state.

    Args:
        request: The incoming FastAPI request.

    Returns:
        The shared ICacheBackend instance.
    """
    return request.app.state.cache_backend


ICacheBackendDep = Annotated[ICacheBackend, Depends(get_cache_backend)]
