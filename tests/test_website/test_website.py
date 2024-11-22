import asyncio

import pytest
from pathlib import Path

import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from website import rdhelper
from website.hcvault import get_config
from website.server import app
from website.middleware import get_context

def save_cookies(user: dict, client: AsyncClient):
    if "cookie" not in user or user["cookie"] is None:
        user["cookie"] = dict()
    user["cookie"].clear()
    for k, v in client.cookies.items():
        user["cookie"][k] = v


def load_cookies(user: dict, client: AsyncClient):
    if "cookie" in user and user["cookie"] is not None:
        for k, v in user["cookie"].items():
            client.cookies.set(k, v)


@pytest_asyncio.fixture
async def test_context():
    alias = "noreply"
    config = await get_config()
    base_url = f'https://{config["webserver"]["domain"][0]}'
    async with AsyncClient(transport=ASGITransport(app=app), base_url=base_url) as client:
        await client.get("/status/ready")
        ctx = get_context(app)
        user = await ctx.vault.kv_get(Path(f"kv/user/{alias}"))
        before = user.copy()
        if user is not None:
            load_cookies(user, client)

        yield client, user
        save_cookies(user, client)
        if before != user:
            await ctx.vault.kv_put(Path(f"kv/user/{alias}"), user)


@pytest.mark.asyncio
async def test_landing_page(test_context):
    client, user = test_context
    ctx = get_context(app)
    try:
        await ctx.rm.get_time()
        resp = await client.get("/")
        assert resp is not None
    except Exception as e:
        raise e

