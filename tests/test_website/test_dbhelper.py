import unittest
from pathlib import Path

from website import dbhelper, rdhelper
from website.session import Context

class TestDBHelper(unittest.IsolatedAsyncioTestCase):

    async def test_db_init(self):
        ctx = Context()
        await ctx.init()

    async def test_ensure_user_exists(self):
        ctx = Context()
        await ctx.init()

        alias = "noreply"
        user = await ctx.vault.kv_get(Path("kv/user")/alias)


        await dbhelper.ensure_user_exists(ctx.db, user["username"])
        dbuser = await dbhelper.get_user_by_username(ctx.db, user["username"])

        t = await rdhelper.get_time(ctx.redis)



        scenario = [
            [dbhelper.PROCEED,    {"count": 9, "limit": 10, "pending": [{"challenge": "abc123", "expire": t-10}]}],
            [dbhelper.EMPTY,      {"count": 10, "limit": 10, "pending": [{"challenge": "abc123", "expire": t-10}]}],
            [dbhelper.PROCEED,    {"count": 0, "limit": 10, "pending": []}],
            [dbhelper.CONTENTION, {"count": 9, "limit": 10, "pending": [{"challenge": "abc123", "expire": t+300}]}],
        ]

        for v in scenario:
            expected = v[0]
            source = v[1]
            for success in [True, False]:
                await ctx.db.user.find_one_and_update(
                    {"_id": dbuser["_id"]},
                    {"$set": {"scan.google": source}},
                    return_document=False
                )

                t = await rdhelper.get_time(ctx.redis)
                ticket = await dbhelper.inc_scan_p1(ctx.db, dbuser["_id"], t)
                assert ticket is not None
                assert expected == ticket["state"]

                if ticket["state"] == dbhelper.PROCEED:
                    await dbhelper.inc_scan_p2(ctx.db, dbuser["_id"], ticket["challenge"], success)
                    result = await ctx.db.user.find_one({"_id": dbuser["_id"]})
                    assert 0 == len(result["scan"]["google"]["pending"])
                    copy = source.copy()
                    assert copy["count"] + (1 if success else 0) == result["scan"]["google"]["count"]
                elif ticket["state"] == dbhelper.CONTENTION:
                    result = await ctx.db.user.find_one({"_id": dbuser["_id"]})
                    c = result["scan"]["google"]["count"]
                    l = result["scan"]["google"]["limit"]
                    assert 0 <= c < l
                    assert l-c == len(result["scan"]["google"]["pending"])
                    break
                elif ticket["state"] == dbhelper.EMPTY:
                    result = await ctx.db.user.find_one({"_id": dbuser["_id"]})
                    c = result["scan"]["google"]["count"]
                    l = result["scan"]["google"]["limit"]
                    assert c == l
                    assert 0 == len(result["scan"]["google"]["pending"])
                    break
