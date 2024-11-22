from uuid import uuid4

from fastapi import FastAPI, Request, Response
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from starlette.middleware.base import BaseHTTPMiddleware

from website import util, rdhelper, dbhelper
from website.dao import ResourceManager, Credit
from website.gmail import GmailClient
from website.gocr import GOCR
from website.hcvault import get_config, VaultClient
from redis.asyncio import Redis

class Context:
    def __init__(self):
        self._init: bool = False
        self.rm = ResourceManager()
        self.vault: VaultClient | None = None
        self.gmail: GmailClient | None = None
        self.gocr: GOCR | None = None
        self.credit: Credit | None = None
        self.timeout: int = 2*86400
        self.user = None

    async def init(self):
        if not self._init:
            self._init = True
            try:
                self.credit = Credit(self.rm)
                await self.rm.setup()
                self.vault = VaultClient.from_config(self.rm.config)
                self.gmail = GmailClient(self.rm.config)
                self.gocr = GOCR(self.rm.config)

                await self.gmail.init()
                await self.gocr.init()
            except Exception as e:
                raise e


SESSION_ID = "SESSION_ID"
class SessionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.ctx = Context()

    async def init(self):
        await self.ctx.init()

    async def dispatch(self, request: Request, call_next):
        await self.init()
        if request.url.path.startswith("/status"):
            return await call_next(request)

        new_session = False
        sid = request.cookies.get(SESSION_ID)
        if not sid or not await self.ctx.rm.redis.exists("/session/"+sid):
            new_session = True
            sid = str(uuid4())
            await self.ctx.rm.redis.set("/session/"+sid, util.to_cbor({}), ex=self.ctx.timeout)

        raw0 = await self.ctx.rm.redis.get("/session/"+sid)
        request.state.session = util.from_cbor(raw0)
        request.state.session["ip"] = request.client.host

        response: Response = await call_next(request)
        if new_session:
            response.set_cookie(SESSION_ID, sid, httponly=True, secure=True, samesite='strict', max_age=self.ctx.timeout)

        raw1 = util.to_cbor(request.state.session)
        if raw0 != raw1:
            await self.ctx.rm.redis.set("/session/"+sid, raw1)

        return response


def get_context(app: FastAPI):
    v = app.middleware_stack
    while True:
        if isinstance(v, SessionMiddleware):
            return v.ctx
        if not hasattr(v, "app"):
            break
        v = v.app
    raise ValueError("unable to get context")


class StaticMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.__init = False
        self.app = app
        self.config = None

    async def init(self):
        if not self.__init:
            self.__init = True
            self.config = await get_config()

    async def dispatch(self, request: Request, call_next):
        await self.init()
        response: Response = await call_next(request)
        if request.url.path.startswith("/static") and not self.config["production"]:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        return response
