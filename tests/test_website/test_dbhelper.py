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
                    t = await rdhelper.get_time(ctx.redis)
                    result = await dbhelper.inc_scan_p2(ctx.db, dbuser["_id"], t, ticket["challenge"], success)
                    assert 0 == len(result["scan"]["google"]["pending"])
                    copy = source.copy()
                    assert copy["count"] + (1 if success else 0) == result["scan"]["google"]["count"]
                elif ticket["state"] == dbhelper.CONTENTION:
                    assert True
                    break
                elif ticket["state"] == dbhelper.EMPTY:
                    assert True
                    break

        pass

