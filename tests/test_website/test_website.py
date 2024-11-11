import unittest

from website import common
from website.hcvault import get_config

class TestWebsite(unittest.IsolatedAsyncioTestCase):

    async def test_config(self):
        config = await get_config()
        self.assertIsNotNone(config)

