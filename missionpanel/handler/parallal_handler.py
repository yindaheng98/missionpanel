import abc
import asyncio
from typing import List

from missionpanel.orm import Mission, Attempt
from .handler import AsyncHandler, HandlerInterface


class ParallelAsyncHandler(AsyncHandler, abc.ABC):
    def __init__(self, n_parallel: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.task_queue = asyncio.Queue(n_parallel)
        for i in range(n_parallel):
            self.task_queue.put_nowait(i)
        self.task_dict = {}
        self.sem_report = asyncio.Semaphore(1)

    async def report_attempt(self, mission: Mission, attempt: Attempt):
        async with self.sem_report:
            await super().report_attempt(mission, attempt)

    async def run_all(self, tags: List[str]):
        async def task(mission: Mission, attempt: Attempt, id: int):
            attempt = await self.watchdog_mission(mission, attempt)
            await self.task_queue.put(id)
            return attempt
        while True:
            id = await self.task_queue.get()
            async with self.sem_report:
                mission = await self.get_mission(tags)
                if mission is None:
                    break
                attempt = HandlerInterface.create_attempt(self.session, mission, self.name, self.max_time_interval)
                self.task_dict[id] = asyncio.create_task(task(mission, attempt, id))
        for i in self.task_dict:
            await self.task_dict[i]
            del self.task_dict[i]
