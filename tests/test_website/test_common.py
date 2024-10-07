import unittest

from website import common


class TestCommon(unittest.TestCase):

    def test_config(self):
        config = common.get_config()
        self.assertIsNotNone(config)


    def test_open_database(self):
        config = common.get_config()
        client, db = common.open_database(config)
        self.assertIsNotNone(client)
        self.assertIsNotNone(db)


    def test_open_redis(self):
        config = common.get_config()
        redis = common.open_redis(config)
        self.assertIsNotNone(redis)
