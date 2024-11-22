import asyncio
from abc import ABC, abstractmethod
import time

from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorClient
from redis.asyncio import Redis
from typing_extensions import override

from website import rdhelper, util, dbhelper
from website.hcvault import get_config


class ResourceManager:
    def __init__(self, gc_interval=3600, task_poll_interval=60):
        self.__setup = False
        self.gc_interval = gc_interval
        self.gc_checkpoint = time.monotonic()
        self.task_poll_interval = task_poll_interval
        self.last_time_sync = 0
        self.time = 0
        self.dao = []
        self.primary = None

        self.config: dict | None = None
        self.client: AsyncIOMotorClient | None = None
        self.db: AsyncIOMotorDatabase | None = None
        self.redis: Redis | None = None

    def register(self, resource):
        if self.__setup:
            raise ValueError("cannot register after setup")
        self.dao.append(resource)

    async def setup(self):
        if self.__setup:
            return

        self.__setup = True
        self.config = await get_config()
        self.client, self.db = util.open_database(self.config)
        self.redis = util.open_redis(self.config)

        t = await self.get_time()
        await dbhelper.init(self.db, t)
        ## setup dao objects
        await asyncio.gather(*[v.setup() for v in self.dao])
        ## start the loop
        self.primary = asyncio.create_task(self._loop())

    async def _loop(self):
        while True:
            now = time.monotonic()
            if now-self.gc_checkpoint > self.gc_interval and await self.is_leader():
                self.gc_checkpoint = now
                self.gc()

            for i in range(len(self.dao) - 1, -1, -1):
                if self.dao[i].task and self.dao[i].task.done():
                    self.dao[i].task = None

            await asyncio.sleep(self.task_poll_interval)

    async def is_leader(self):
        return True

    def gc(self):
        for resource in self.dao:
            if resource.task is None or resource.task.done():
                resource.task = asyncio.create_task(resource.gc())

    def teardown(self):
        asyncio.gather(*[v.teardown() for v in self.dao], return_exceptions=True)
        asyncio.gather(*[v.task for v in self.dao], return_exceptions=True)

    async def get_time(self):
        now = time.monotonic()
        delta = now-self.last_time_sync
        if delta >= 1:
            self.last_time_sync = now
            self.time = await rdhelper.get_time(self.redis)
            delta = 0
        return self.time+delta


class Resource:
    def __init__(self, rm: ResourceManager):
        self.rm = rm
        self.rm.register(self)

    @abstractmethod
    async def setup(self):
        pass

    @abstractmethod
    async def gc(self):
        pass

    @abstractmethod
    async def teardown(self):
        pass


class Credit(Resource):
    def __init__(self, rm: ResourceManager):
        super().__init__(rm)

    @override
    async def setup(self):
        pass

    @override
    async def gc(self):
        pass

    @override
    async def teardown(self):
        pass

    async def debit_p1(self):
        pass

    async def debit_p2(self):
        pass
