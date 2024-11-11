from uuid import uuid4

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from website import common, rdhelper
from website.gmail import GmailClient

SESSION_ID = "SESSION_ID"
class SessionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI):
        super().__init__(app)
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
                self.config = await common.get_config()
                v = common.open_database(self.config)
                self.client = v[0]
                self.db = v[1]
                self.redis = common.open_redis(self.config)
                self.gmail = GmailClient(self.config)
                self.timeout = 2*86400

                col_log = self.db.get_collection("log")
                t = await rdhelper.get_time(self.redis)
                await col_log.insert_one({"boot": t})
                await self.gmail.init()
            except Exception as e:
                raise e

    async def dispatch(self, request: Request, call_next):
        await self.init()
        if request.url.path.startswith("/status"):
            return await call_next(request)

        new_session = False
        sid = request.cookies.get(SESSION_ID)
        if not sid or not await self.redis.exists("/session/"+sid):
            new_session = True
            sid = str(uuid4())
            await self.redis.set("/session/"+sid, common.to_cbor({}), ex=self.timeout)

        raw0 = await self.redis.get("/session/"+sid)
        request.state.session = common.from_cbor(raw0)
        request.state.session["ip"] = request.client.host

        response: Response = await call_next(request)
        if new_session:
            response.set_cookie(SESSION_ID, sid, httponly=True, secure=True, samesite='strict', max_age=self.timeout)

        raw1 = common.to_cbor(request.state.session)
        if raw0 != raw1:
            await self.redis.set("/session/"+sid, raw1)

        return response


def get_session(app: FastAPI):
    v = app.middleware_stack
    while True:
        if isinstance(v, SessionMiddleware):
            return v
        if not hasattr(v, "app"):
            break
        v = v.app
