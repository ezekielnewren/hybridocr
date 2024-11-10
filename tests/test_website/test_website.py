import unittest

from website import common


class TestWebsite(unittest.IsolatedAsyncioTestCase):

    async def test_config(self):
        config = await common.get_config()
        self.assertIsNotNone(config)

    async def test_gmail_read(self):
        config = await common.get_config()
        result = await common.list_email(config, "noreply")

        self.assertIsNotNone(result)



