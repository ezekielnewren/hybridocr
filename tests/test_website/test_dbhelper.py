import unittest
from pathlib import Path

from website import dbhelper, rdhelper
from website.session import Context

class TestDBHelper(unittest.IsolatedAsyncioTestCase):

    async def test_db_init(self):
        ctx = Context()
        await ctx.init()

    async def test_user_upsert(self):
        ctx = Context()
        await ctx.init()

        alias = "noreply"
        user = await ctx.vault.kv_get(Path("kv/user")/alias)


        await dbhelper.upsert_user(ctx.db, user["username"])
        dbuser = await dbhelper.get_user_by_username(ctx.db, user["username"])

        t = await rdhelper.get_time(ctx.redis)

        for success in [True, False]:
            ticket = await dbhelper.inc_scan_p1(ctx.db, dbuser["_id"], t)
            if ticket is None:
                print("no more scans left")
            elif ticket and ticket["contention"]:
                print("last scan(s) contention, retry")
            else:
                print("proceed with scan")
                t = await rdhelper.get_time(ctx.redis)
                await dbhelper.inc_scan_p2(ctx.db, dbuser["_id"], t, ticket["challenge"], success)

        pass

