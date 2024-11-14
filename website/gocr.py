import json
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.cloud import vision
from google.auth.credentials import Credentials

from website.hcvault import VaultClient


class GOCR(Credentials):
    ALIAS = "hybridocr-sa"
    def __init__(self, config):
        super().__init__()
        self.__init = False
        self.vault = VaultClient.from_config(config)
        self.cred = None

    async def refresh(self, req: Request):
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
            cred.refresh(req)
            await self.vault.kv_put(Path("kv/oauth_token")/GOCR.ALIAS, {"token": cred.token})

        self.cred = cred

    async def ocr(self, image):
        client = vision.ImageAnnotatorClient(credentials=self)
        pass
