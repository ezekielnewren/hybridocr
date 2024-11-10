import aiohttp
import json
from pathlib import Path

from aiohttp import ClientResponse

from website import common


class ResponseWithContent:
    def __init__(self, response: ClientResponse, content: bytes):
        self.response = response
        self.content = content


class VaultClient:
    API_VERSION = "v1"

    def __init__(self, _addr, _token):
        self.addr = _addr
        self.token = _token

    @staticmethod
    async def _check_response(r: ClientResponse, error_on_warnings=False, raw=False):
        content = await r.content.read()
        if r.status // 100 != 2:
            message = str(r.url) + " " + str(content, "utf-8")
            raise IOError(ResponseWithContent(r, content), message)
        if r.status == 204:
            return None
        if not raw:
            try:
                content = json.loads(content)
            except json.decoder.JSONDecodeError as e:
                return content
            if "errors" in content:
                raise IOError(r, content["errors"])
            if error_on_warnings and content["warnings"] is not None:
                raise IOError(r, content["warnings"])
        return content

    async def _request(self, request_type, path, body, raw=False):
        common.check_type(path, Path)
        headers = dict()
        headers["Content-Type"] = "application/json"
        headers["X-Vault-Request"] = "true"
        headers["X-Vault-Token"] = self.token

        url = self.addr+str(Path("/"+VaultClient.API_VERSION)/path)
        payload = None if body is None else common.compact_json(body)
        async with aiohttp.request(request_type, url, headers=headers, data=payload) as response:
            return await self._check_response(response, raw=raw)

    async def read_raw(self, path):
        return await self._request("GET", path, body=None, raw=True)

    async def read(self, path):
        return await self._request("GET", path, body=None)

    async def write(self, path, **kwargs):
        return await self._request("PUT", path, body=kwargs)

    async def post(self, path, **kwargs):
        return await self._request("POST", path, body=kwargs)

    async def kv_get(self, path: Path):
        u = path.parent/"data"/path.name
        try:
            r = await self.read(u)
            return r["data"]["data"]
        except IOError as e:
            r: ResponseWithContent = e.errno
            c = json.loads(r.content)
            if r.response.status == 404 and "errors" in c and len(c["errors"]) == 0:
                raise KeyError(str(path.name))
            raise e

    async def kv_put(self, path, data):
        u = path.parent/"data"/path.name
        common.check_type(data, dict)
        return await self.write(u, **{"data": data})

    @classmethod
    def from_config(cls, config):
        return VaultClient(config["vault"]["VAULT_ADDR"], config["vault"]["VAULT_TOKEN"])
