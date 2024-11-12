import asyncio
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from website.server import app
from website.session import get_context

@pytest.fixture(scope="module")
async def test_context():
    with TestClient(app) as client:
        client.get("/status/ready")
        ctx = get_context(app)
        user = await ctx.vault.kv_get(Path(f"kv/user/noreply"))
        if user is not None and "cookie" in user and isinstance(user["cookie"], dict):
            for k, v in user.items():
                client.cookies.set(k, v)
        yield client, user


@pytest.mark.asyncio
async def test_landing_page(test_context):
    client, user = await anext(test_context)
    resp = client.get("/")

    assert resp is not None
