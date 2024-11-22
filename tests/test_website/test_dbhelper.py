import unittest
from pathlib import Path

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from website import dbhelper, rdhelper, util
from website.middleware import Context

class TestDBHelper(unittest.IsolatedAsyncioTestCase):

    async def test_db_init(self):
        ctx = Context()
        await ctx.init()

    async def test_credit_debit(self):
        ctx = Context()
        await ctx.init()

        alias = "noreply"
        user = await ctx.vault.kv_get(Path("kv/user")/alias)


        t = await ctx.rm.get_time()
        await dbhelper.ensure_user_exists(ctx.rm.db, t, user["username"])
        dbuser = await dbhelper.get_user_by_username(ctx.rm.db, user["username"])


        ym = util.year_month_str(t)
        


        scenario = [
            [dbhelper.PROCEED,    {"history":{},"monthly":{"value":10,"reset":t-86400},"wallet":0,"ledger":[[t-7,10]],"pending":[{"challenge": "abc123", "expire": t+300}],"cas":util.new_cas()}],
            [dbhelper.PROCEED,    {"history":{ym:10},"monthly":{"value":0,"reset":t-86400},"wallet":10,"ledger":[[t-7,10]],"pending":[],"cas":util.new_cas()}],
            [dbhelper.EMPTY,      {"history":{ym:10},"monthly":{"value":0,"reset":t-86400},"wallet":0,"ledger":[[t-7,10]],"pending":[],"cas":util.new_cas()}],
            [dbhelper.PROCEED,    {"history":{ym:10},"monthly":{"value":1,"reset":t-86400},"wallet":0,"ledger":[[t-7,10]],"pending":[],"cas":util.new_cas()}],
            [dbhelper.CONTENTION, {"history":{ym:10},"monthly":{"value":1,"reset":t-86400},"wallet":0,"ledger":[[t-7,10]],"pending":[{"challenge": "abc123", "expire": t+300}],"cas":util.new_cas()}],
            [dbhelper.CONTENTION, {"history":{ym:10},"monthly":{"value":0,"reset":t-86400},"wallet":1,"ledger":[[t-7,10]],"pending":[{"challenge": "abc123", "expire": t+300}],"cas":util.new_cas()}],
        ]


        col_user: AsyncIOMotorCollection = ctx.rm.db.user
        for v in scenario:
            expected = v[0]
            source = v[1]
            for success in [True, False]:
                await col_user.find_one_and_update(
                    {"_id": dbuser["_id"]},
                    {"$set": {"credit": source}},
                    return_document=False
                )

                ticket = await ctx.credit.debit_p1(dbuser["_id"])
                assert ticket is not None
                assert expected == ticket["state"]

                if ticket["state"] == dbhelper.PROCEED:
                    await ctx.credit.debit_p2(dbuser["_id"], ticket["challenge"], success)
                    result = await col_user.find_one({"_id": dbuser["_id"]})
                    assert len(source["pending"]) == len(result["credit"]["pending"])
                    assert source["monthly"]["value"] - (1 if success and source["monthly"]["value"]>0 else 0) == result["credit"]["monthly"]["value"]
                    assert source["wallet"] - (1 if success and source["monthly"]["value"]<=0 else 0) == result["credit"]["wallet"]
                elif ticket["state"] in [dbhelper.CONTENTION, dbhelper.EMPTY]:
                    result = await col_user.find_one({"_id": dbuser["_id"]})
                    assert len(source["pending"]) == len(result["credit"]["pending"])
                    assert source["monthly"]["value"] == result["credit"]["monthly"]["value"]
                    assert source["wallet"] == result["credit"]["wallet"]
                    break

