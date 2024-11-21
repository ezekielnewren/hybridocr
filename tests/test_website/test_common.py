import unittest

from website.hcvault import get_config
from website import util

class TestCommon(unittest.IsolatedAsyncioTestCase):

    async def test_config(self):
        config = await get_config()
        self.assertIsNotNone(config)


    async def test_open_database(self):
        config = await get_config()
        client, db = util.open_database(config)
        self.assertIsNotNone(client)
        self.assertIsNotNone(db)


    async def test_open_redis(self):
        config = await get_config()
        redis = util.open_redis(config)
        self.assertIsNotNone(redis)
