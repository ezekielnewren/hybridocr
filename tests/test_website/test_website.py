import unittest

from website import common


class TestWebsite(unittest.TestCase):

    def test_config(self):
        config = common.get_config()
        self.assertIsNotNone(config)

    def test_gmail_read(self):
        config = common.get_config()
        common.list_email(config, "noreply")

        pass



