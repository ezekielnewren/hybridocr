import unittest

from website import common
from website.gmail import GmailClient


class TestWebsite(unittest.IsolatedAsyncioTestCase):

    async def test_config(self):
        config = await common.get_config()
        self.assertIsNotNone(config)

