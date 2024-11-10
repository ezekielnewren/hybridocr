import unittest

from website import common
from website.gmail import GmailClient


class TestWebsite(unittest.IsolatedAsyncioTestCase):

    async def test_config(self):
        config = await common.get_config()
        self.assertIsNotNone(config)

    async def test_gmail_read(self):
        config = await common.get_config()
        gmail = GmailClient(config)
        result = await gmail.list_email("noreply")

        self.assertIsNotNone(result)



