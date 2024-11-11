from uuid import uuid4

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from website import common, rdhelper, dbhelper
from website.gmail import GmailClient
from website.hcvault import get_config

class Context:
    def __init__(self):
        self._init = False
        self.config = None
        self.client = None
        self.db = None
        self.redis = None
        self.gmail = None
        self.timeout = None

    async def init(self):
        if not self._init:
            self._init = True
            try:
                self.config = await get_config()
                self.client, self.db = common.open_database(self.config)
                self.redis = common.open_redis(self.config)
                self.gmail = GmailClient(self.config)
                self.timeout = 2*86400

                t = await rdhelper.get_time(self.redis)
                await dbhelper.init(self.db, t)
                await self.gmail.init()
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
        if not sid or not await self.ctx.redis.exists("/session/"+sid):
            new_session = True
            sid = str(uuid4())
            await self.ctx.redis.set("/session/"+sid, common.to_cbor({}), ex=self.ctx.timeout)

        raw0 = await self.ctx.redis.get("/session/"+sid)
        request.state.session = common.from_cbor(raw0)
        request.state.session["ip"] = request.client.host

        response: Response = await call_next(request)
        if new_session:
            response.set_cookie(SESSION_ID, sid, httponly=True, secure=True, samesite='strict', max_age=self.timeout)

        raw1 = common.to_cbor(request.state.session)
        if raw0 != raw1:
            await self.ctx.redis.set("/session/"+sid, raw1)

        return response


def get_context(app: FastAPI):
    v = app.middleware_stack
    while True:
        if isinstance(v, SessionMiddleware):
            return v.ctx
        if not hasattr(v, "app"):
            break
        v = v.app
