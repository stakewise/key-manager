import asyncio
from functools import wraps
from typing import Callable


def async_command(f):
    """Decorator to run asyncio click commands"""

    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


def async_multiprocessing_proxy(
    f: Callable,
    *args,
    **kwargs,
):
    """Proxy to run asyncio coroutines with multiprocessing pool"""
    return asyncio.run(f(*args, **kwargs))


def chunkify(items, size):
    for i in range(0, len(items), size):
        yield items[i : i + size]
