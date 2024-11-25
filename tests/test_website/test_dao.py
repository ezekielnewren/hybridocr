import pytest

from website.middleware import Context


@pytest.mark.asyncio
async def test_update_trial_credits():
    ctx = Context()
    await ctx.init()

    await ctx.credit.get_trial_balance()

    pass