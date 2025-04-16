import abc
import asyncio
import datetime
from typing import List, Optional, Tuple, Union
from sqlalchemy.orm import Session, Query
from sqlalchemy.ext.asyncio import AsyncSession
from missionpanel.orm import Mission, Tag, MissionTag, Attempt
from sqlalchemy import select, func, distinct, case, Select


class HandlerInterface(abc.ABC):

    @staticmethod
    def query_missions_by_tag(tags: List[str]) -> Select[Tuple[Mission]]:
        return (
            select(Mission)
            .join(MissionTag)
            .join(Tag)
            .filter(Tag.name.in_(tags))
            .group_by(Mission.id)
            .having(func.count(distinct(Tag.name)) == len(tags))
        )

    @staticmethod
    def query_todo_missions(tags: List[str]) -> Select[Tuple[Mission]]:
        return (
            HandlerInterface.query_missions_by_tag(tags)
            .outerjoin(Attempt)
            .group_by(Mission.id)
            .having(func.count(
                case(((  # see if Attempt is finished or working on the Mission
                    Attempt.success.is_(True) |  # have finished handler
                    (Attempt.last_update_time + Attempt.max_time_interval >= datetime.datetime.now())  # have working handler
                ), 0), else_=None)) <= 0)  # get those Missions that have no finished or working Attempt
        )

    @staticmethod
    def create_attempt(session: Union[Session | AsyncSession], mission: Mission, name: str, max_time_interval: datetime.timedelta = datetime.timedelta(seconds=1)) -> Attempt:
        attempt = Attempt(
            handler=name,
            max_time_interval=max_time_interval,
            content=mission.content,
            mission=mission)
        session.add(attempt)
        return attempt


class Handler(HandlerInterface, abc.ABC):
    def __init__(self, session: Session, name: str, max_time_interval: datetime.timedelta = datetime.timedelta(seconds=1)):
        self.session = session
        self.name = name
        self.max_time_interval = max_time_interval

    @abc.abstractmethod
    def select_mission(self, missions: Query[Mission]) -> Optional[Mission]:
        return missions[0] if missions else None

    def report_attempt(self, mission: Mission, attempt: Attempt):
        attempt.success = False
        attempt.last_update_time = datetime.datetime.now()
        self.session.commit()

    @abc.abstractmethod
    def execute_mission(self, mission: Mission, attempt: Attempt) -> bool:
        pass

    def run_once(self, tags: List[str]):
        missions = self.session.execute(HandlerInterface.query_todo_missions(tags)).scalars().all()
        mission = self.select_mission(missions)
        if mission is None:
            return
        attempt = HandlerInterface.create_attempt(self.session, mission, self.name, self.max_time_interval)
        self.report_attempt(mission, attempt)
        if self.execute_mission(mission, attempt):
            attempt.success = True
        self.report_attempt(mission, attempt)
        return attempt


class AsyncHandler(HandlerInterface, abc.ABC):
    def __init__(self, session: AsyncSession, name: str, max_time_interval: datetime.timedelta = datetime.timedelta(seconds=1)):
        self.session = session
        self.name = name
        self.max_time_interval = max_time_interval

    @abc.abstractmethod
    async def select_mission(self, missions: Query[Mission]) -> Optional[Mission]:
        return missions[0] if missions else None

    async def report_attempt(self, mission: Mission, attempt: Attempt):
        attempt.last_update_time = datetime.datetime.now()
        await self.session.commit()
        await self.session.refresh(attempt)
        await self.session.refresh(mission)

    @abc.abstractmethod
    async def execute_mission(self, mission: Mission, attempt: Attempt) -> bool:
        pass

    async def get_mission(self, tags: List[str]) -> Optional[Mission]:
        missions = (await self.session.execute(HandlerInterface.query_todo_missions(tags))).scalars().all()
        return await self.select_mission(missions)

    async def watchdog_mission(self, mission: Mission, attempt: Attempt):
        await self.report_attempt(mission, attempt)
        task = asyncio.create_task(self.execute_mission(mission, attempt))
        while not task.done():
            await self.report_attempt(mission, attempt)
            await asyncio.sleep(self.max_time_interval.total_seconds() / 2)
        if task.result():
            attempt.success = True
        await self.report_attempt(mission, attempt)
        return attempt

    async def run_mission(self, mission: Mission):
        attempt = HandlerInterface.create_attempt(self.session, mission, self.name, self.max_time_interval)
        return await self.watchdog_mission(mission, attempt)

    async def run_once(self, tags: List[str]):
        mission = await self.get_mission(tags)
        if mission is None:
            return
        return await self.run_mission(mission)

    async def run_all(self, tags: List[str]):
        while await self.run_once(tags):
            pass
