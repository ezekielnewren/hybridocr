import unittest

from website import common


class TestWebsite(unittest.TestCase):

    def test_config(self):
        config = common.get_config()
        self.assertIsNotNone(config)
