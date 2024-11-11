import unittest

from website import common
from website.hcvault import get_config, VaultClient
from pathlib import Path

class TestHcvault(unittest.IsolatedAsyncioTestCase):

    async def test_vault_status(self):
        config = await get_config()

        vault = VaultClient(config["vault"]["VAULT_ADDR"], config["vault"]["VAULT_TOKEN"])

        result = await vault.read("sys/seal-status")

        self.assertIsNotNone(result)

    async def test_get_config(self):
        config = await get_config()

        self.assertIsNotNone(config)


    async def test_kv_put(self):
        config = await get_config()

        vault = VaultClient.from_config(config)

        obj = {"key": "value"}
        await vault.kv_put(Path("kv/oauth_token/test"), obj)

        r = await vault.kv_get(Path("kv/oauth_token/test"))

        self.assertEqual(obj, r)