import pytest

from benjaminhamon_standard_extensions.asyncio_extensions.asyncio_context import AsyncioContext


@pytest.mark.asyncio
async def test_run_async() -> None:

    async def coroutine() -> None:
        pass

    asyncio_context = AsyncioContext()
    await asyncio_context.run_async(coroutine())


@pytest.mark.asyncio
async def test_run_async_with_exception() -> None:

    async def coroutine() -> None:
        raise RuntimeError

    asyncio_context = AsyncioContext()

    with pytest.raises(RuntimeError):
        await asyncio_context.run_async(coroutine())


@pytest.mark.asyncio
async def test_run_async_with_keyboard_interrupt() -> None:
    pytest.skip() # Raising KeyboardInterrupt cause pytest to stop

    async def coroutine() -> None:
        raise KeyboardInterrupt

    asyncio_context = AsyncioContext()

    with pytest.raises(KeyboardInterrupt):
        await asyncio_context.run_async(coroutine())
