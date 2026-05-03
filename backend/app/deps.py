from typing import AsyncGenerator


async def get_db() -> AsyncGenerator[None, None]:
    yield None


async def get_current_user() -> dict:
    return {}
