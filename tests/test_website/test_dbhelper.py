import unittest

from website.session import Context

class TestDBHelper(unittest.IsolatedAsyncioTestCase):

    async def test_db_init(self):
        ctx = Context()
        await ctx.init()


