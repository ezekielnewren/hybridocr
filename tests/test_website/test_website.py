import asyncio
from pathlib import Path

import pytest
from httpx import Response, Cookies
from starlette.testclient import TestClient

from website.server import app
from website.session import get_context


def save_cookies(user: dict, client: TestClient):
    if "cookie" not in user or user["cookie"] is None:
        user["cookie"] = dict()
    user["cookie"].clear()
    for k, v in client.cookies.items():
        user["cookie"][k] = v


def load_cookies(user: dict, client: TestClient):
    if "cookie" in user and user["cookie"] is not None:
        for k, v in user["cookie"].items():
            client.cookies.set(k, v)


@pytest.fixture(scope="module")
async def test_context():
    client = TestClient(app):
    client.get("/status/ready")
    ctx = get_context(app)
    username = "noreply"
    user = await ctx.vault.kv_get(Path(f"kv/user/{username}"))
    if user is not None:
        load_cookies(user, client.cookies)

    yield client, user

    save_cookies(user, client)
    await ctx.vault.kv_put(Path(f"kv/user/{username}"), user)
    client.close()


@pytest.mark.asyncio
async def test_landing_page(test_context):
    client, user = await anext(test_context)
    client: TestClient = client

    resp: Response = client.get("/")

    assert resp is not None
