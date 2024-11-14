import pytest

from website.gocr import GOCR
from website.hcvault import get_config
from google.auth.transport.requests import Request

@pytest.mark.asyncio
async def test_gocr_init():
    config = await get_config()
    try:
        gocr = GOCR(config)
        await gocr.refresh(Request())
        await gocr.refresh(Request())
    except Exception as e:
        raise e

