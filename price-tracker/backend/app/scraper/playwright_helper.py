"""
Playwright helper — runs Playwright in a separate thread with its own ProactorEventLoop.

On Windows, uvicorn uses SelectorEventLoop which doesn't support
asyncio.create_subprocess_exec (required by Playwright). We work around
this by running Playwright in a dedicated thread with a ProactorEventLoop.
"""

import asyncio
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Any

# Shared thread pool for Playwright operations
_playwright_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="playwright")


def _run_in_new_loop(coro_fn: Callable, *args) -> Any:
    """Run an async function in a brand-new event loop (ProactorEventLoop on Windows)."""
    if sys.platform == "win32":
        loop = asyncio.ProactorEventLoop()
    else:
        loop = asyncio.new_event_loop()

    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro_fn(*args))
    finally:
        loop.close()


async def run_playwright_scrape(coro_fn: Callable, *args) -> Any:
    """
    Schedule a Playwright coroutine to run in a separate thread with a
    ProactorEventLoop, making it compatible with Windows + uvicorn.

    Usage:
        result = await run_playwright_scrape(my_scrape_coro, url)
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        _playwright_executor,
        _run_in_new_loop,
        coro_fn,
        *args,
    )
