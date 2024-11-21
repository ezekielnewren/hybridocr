import unittest

from website import util
from website.hcvault import get_config
from website.gmail import GmailClient
from datetime import datetime

class TestGmail(unittest.IsolatedAsyncioTestCase):

    async def test_list(self):
        config = await get_config()
        gmail = GmailClient(config)
        result = await gmail.list_email("noreply")

        self.assertIsNotNone(result)

    async def test_send_email(self):
        config = await get_config()

        gmail = GmailClient(config)
        sender = "noreply"
        recipient = f"{sender}@{util.DOMAIN}"
        subject = "Test subject"
        body = str(datetime.now())
        await gmail.send_email(sender, recipient, subject, body)
