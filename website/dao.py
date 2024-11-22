import asyncio
import random
from abc import ABC, abstractmethod
import time

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorClient, AsyncIOMotorCollection
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
        self.background_list = []
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

            for v in self.dao:
                if v.task is not None and v.task.done():
                    v.task = None

            for i in range(len(self.background_list)-1, -1, -1):
                if self.background_list[i].done():
                    del self.background_list[i]

            await asyncio.sleep(self.task_poll_interval)

    def background(self, coroutine):
        task = asyncio.create_task(coroutine)
        self.background_list.append(task)


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
        self.task = None

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
        self.col_user: AsyncIOMotorCollection | None = None

    @override
    async def setup(self):
        self.col_user = self.rm.db.user

    @override
    async def gc(self):
        t = await self.rm.get_time()
        await self.col_user.update_many(
            {},
            {
                "$pull": {
                    "credit.pending": {
                        "expire": {"$lt": t}
                    }
                }
            }
        )

    @override
    async def teardown(self):
        pass

    async def debit_p1(self, _id: ObjectId, challenge=None):
        if challenge is None:
            challenge = util.generate_alphanumeric(32)

        for attempt in range(10):
            t = await self.rm.get_time()
            ticket = {
                "challenge": challenge,
                "expire": t + 300
            }

            ym = util.year_month_str(t)

            ## read
            result = await self.col_user.find_one({"_id": _id})
            if "credit" not in result:
                starting = 10
                credit = {
                    "history": {
                        ym: 0,
                    },
                    "monthly": {
                        "value": 0,
                        "reset": 0,
                    },
                    "wallet": starting,
                    "ledger": [t, starting],
                    "pending": [],
                    "cas": util.new_cas(),
                }
                await self.col_user.find_one_and_update(
                    {"_id": _id, "credit": {"$exists": False}},
                    {"$set": {"credit": credit}},
                )
                continue
            credit = result["credit"]

            ## modify
            credit["pending"] = [v for v in credit["pending"] if t < v["expire"]]
            pending = len(credit["pending"])

            balance = credit["monthly"]["value"]
            balance += credit["wallet"]

            if balance <= 0:
                return {"state": dbhelper.EMPTY}
            elif balance - pending <= 0:
                assert pending > 0
                return {"state": dbhelper.CONTENTION}
            else:
                credit["pending"].append(ticket)

            ## write
            current_cas = credit["cas"]
            credit["cas"] = util.new_cas()
            r = await self.col_user.find_one_and_update(
                {"_id": _id, "credit.cas": current_cas},
                {"$set": {"credit": credit}}
            )

            if r is not None:
                assert balance - pending > 0
                ticket["state"] = dbhelper.PROCEED
                return ticket

            await asyncio.sleep(0.1 * (2 ** attempt) + random.uniform(0, 0.1))

        return {"state": dbhelper.CONTENTION}

    async def debit_p2(self, _id: ObjectId, challenge, commit):
        if commit:
            for attempt in range(10):
                t = await self.rm.get_time()
                ym = util.year_month_str(t)

                ## read
                result = await self.col_user.find_one({"_id": _id})
                credit = result["credit"]

                if credit["monthly"]["value"] > 0:
                    credit["monthly"]["value"] -= 1
                elif credit["wallet"] > 0:
                    credit["wallet"] -= 1
                else:
                    credit["monthly"]["value"] -= 1

                if ym not in credit["history"]:
                    credit["history"][ym] = 0
                credit["history"][ym] += 1

                credit["pending"] = [v for v in credit["pending"] if v["challenge"] != challenge]

                current_cas = credit["cas"]
                credit["cas"] = util.new_cas()
                result = await self.col_user.find_one_and_update(
                    {"_id": _id, "credit.cas": current_cas},
                    {"$set": {"credit": credit}}
                )

                if result is not None:
                    break

                await asyncio.sleep(0.1 * (2 ** attempt) + random.uniform(0, 0.1))
        else:
            await self.col_user.find_one_and_update(
                {"_id": _id},
                {
                    "$pull": {"credit.pending": {"challenge": challenge}}
                }
            )

