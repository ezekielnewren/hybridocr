import asyncio
import unittest
from pathlib import Path

from starlette.testclient import TestClient

from website.hcvault import get_config, VaultClient
from website.server import app
from website.session import get_context



class TestWebsite(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await self.init()

    async def init(self):
        self.user = "noreply"
        config = await get_config()
        vault = VaultClient.from_config(config)
        self.user: dict = await vault.kv_get(Path(f"kv/user/{self.user}"))

        self.client = TestClient(app)
        self.client.get("/status/ready")
        self.ctx = get_context(app)
        await self.ctx.init()
        if self.user is not None and "cookie" in self.user and isinstance(self.user["cookie"], dict):
            for k, v in self.user.items():
                self.client.cookies.set(k, v)

    def tearDown(self):
        self.client.close()

    def test_landing_page(self):
        resp = self.client.get("/")

        self.assertIsNotNone(resp)
