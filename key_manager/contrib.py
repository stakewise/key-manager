import asyncio
import collections
from base64 import b64decode, b64encode
from functools import wraps


def async_command(f):
    """Decorator to run asyncio click commands"""

    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


def bytes_to_str(value: bytes) -> str:
    return b64encode(value).decode('ascii')


def str_to_bytes(value: str) -> bytes:
    return b64decode(value)


def is_lists_equal(x: list, y: list) -> bool:
    return collections.Counter(x) == collections.Counter(y)
