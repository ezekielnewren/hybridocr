from pathlib import Path
import aiohttp
import asyncio


class VaultClient:
    API_VERSION = "v1"

    def __init__(self, _addr, _token):
        self.addr = _addr
        self.token = _token

    async def _request(self, request_type, path, **kwargs):
        if kwargs is None:
            kwargs = {}
        if "headers" not in kwargs:
            kwargs["headers"] = {}
        kwargs["headers"]["X-Vault-Request"] = "true"
        kwargs["headers"]["X-Vault-Token"] = self.token

        prefix = self.addr+"/"+VaultClient.API_VERSION+"/"
        async with aiohttp.request(request_type, prefix+path, **kwargs) as response:
            return await response.text()

    async def read(self, path, **kwargs):
        return await self._request("GET", path, **kwargs)
