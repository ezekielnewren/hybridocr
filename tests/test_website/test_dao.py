import pytest

from website import dbhelper
from website.middleware import Context


@pytest.mark.asyncio
async def test_update_trial_credits():
    ctx = Context()
    await ctx.init()

    t = await ctx.rm.get_time()
    trial_balance = await ctx.credit.get_trial_balance(t)
    trial_limit = await ctx.credit.get_trial_limit(t)


    doc = await ctx.rm.db.user.find_one({'username': "noreply@hybridocr.com"})

    ticket = await ctx.credit.debit_p1(doc["_id"])
    if ticket["state"] == dbhelper.PROCEED:
        await ctx.credit.debit_p2(doc["_id"], ticket["challenge"], True)
    pass
