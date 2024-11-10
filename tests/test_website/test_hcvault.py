import unittest

from website import common
from website.hcvault import VaultClient


class TestHcvault(unittest.IsolatedAsyncioTestCase):

    async def test_vault_status(self):
        config = common.get_config()

        vault = VaultClient(config["vault"]["VAULT_ADDR"], config["vault"]["VAULT_TOKEN"])

        result = await vault.read("sys/seal-status")

        self.assertIsNotNone(result)


