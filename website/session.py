from uuid import uuid4

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from website import common

SESSION_ID = "SESSION_ID"
class SessionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.config = common.get_config()
        self.redis = common.open_redis(self.config)
        v = common.open_database(self.config)
        self.client = v[0]
        self.db = v[1]
        self.timeout = 2*86400

    async def dispatch(self, request: Request, call_next):
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
