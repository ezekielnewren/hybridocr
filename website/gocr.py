import asyncio
import json
from pathlib import Path

from google.auth.transport.requests import Request
from google.cloud.vision_v1 import AnnotateImageResponse
from google.oauth2 import service_account
from google.cloud import vision
from google.auth.credentials import Credentials

from website import common
from website.hcvault import VaultClient


class GOCR(Credentials):
    ALIAS = "hybridocr-sa"
    def __init__(self, config):
        super().__init__()
        self.__init = False
        self.vault = VaultClient.from_config(config)
        self.cred = None

    async def init(self, req: Request = None):
        if self.cred is not None and self.cred.valid:
            return

        t0 = await self.vault.kv_get(Path("kv/oauth_cred")/GOCR.ALIAS)
        cred = service_account.Credentials.from_service_account_info(t0, scopes=["https://www.googleapis.com/auth/cloud-vision"])
        try:
            t1 = await self.vault.kv_get(Path("kv/oauth_token")/GOCR.ALIAS)
            cred.token = t1["token"]
        except KeyError:
            pass

        if cred.token is None or (cred.token is not None and not cred.valid):
            if req is None:
                req = Request()
            cred.refresh(req)
            await self.vault.kv_put(Path("kv/oauth_token")/GOCR.ALIAS, {"token": cred.token})

        self.cred = cred

    def refresh(self, req: Request):
        asyncio.get_event_loop().run_until_complete(self.init(req))

    @property
    def token(self):
        if self.cred is None:
            return None
        return self.cred.token

    @token.setter
    def token(self, value):
        pass

    async def ocr(self, image):
        client = vision.ImageAnnotatorClient(credentials=self)
        img = vision.Image(content=image)
        answer = client.text_detection(image=img)
        return common.compact_json(AnnotateImageResponse.to_json(answer)).encode("utf-8")
