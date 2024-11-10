import unittest

from website import common
from website.gmail import GmailClient


class TestGmail(unittest.IsolatedAsyncioTestCase):

    async def test_list(self):
        config = await common.get_config()
        gmail = GmailClient(config)
        result = await gmail.list_email("noreply")

        self.assertIsNotNone(result)
