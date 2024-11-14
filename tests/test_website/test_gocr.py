import pytest

from tests import open_test_file
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


@pytest.mark.asyncio
async def test_gocr_ocr():
    config = await get_config()
    try:
        gocr = GOCR(config)
        with open_test_file("JWST-000.jpg") as fd:
            image = fd.read()
        interactive = False
        if interactive:
            results = await gocr.ocr(image)
        pass
    except Exception as e:
        raise e
