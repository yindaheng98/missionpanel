import abc
import datetime
from typing import List, Optional, Tuple
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
    def create_attempt(session: Session, mission: Mission, name: str, max_time_interval: datetime.timedelta = datetime.timedelta(seconds=1)) -> Attempt:
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

    @abc.abstractmethod
    def execute_mission(self, mission: Mission, attempt: Attempt) -> bool:
        pass

    def run_once(self, tags: List[str]):
        missions = self.session.execute(HandlerInterface.query_todo_missions(tags)).scalars().all()
        mission = self.select_mission(missions)
        if mission is None:
            return
        attempt = HandlerInterface.create_attempt(self.session, mission, self.name, self.max_time_interval)
        self.session.commit()
        if self.execute_mission(mission, attempt):
            attempt.success = True
        self.session.commit()
        return attempt


class AsyncHandler(HandlerInterface, abc.ABC):
    def __init__(self, session: AsyncSession, name: str, max_time_interval: datetime.timedelta = datetime.timedelta(seconds=1)):
        self.session = session
        self.name = name
        self.max_time_interval = max_time_interval

    @abc.abstractmethod
    async def select_mission(self, missions: Query[Mission]) -> Optional[Mission]:
        return missions[0] if missions else None

    @abc.abstractmethod
    async def execute_mission(self, mission: Mission, attempt: Attempt) -> bool:
        pass

    async def run_once(self, tags: List[str]):
        missions = (await HandlerInterface.query_todo_missions(tags)).all()
        mission = await self.select_mission(missions)
        if mission is None:
            return
        async with self.session.begin():
            attempt = HandlerInterface.create_attempt(self.session, mission, self.name, self.max_time_interval)
        await self.session.commit()
        if await self.execute_mission(mission, attempt):
            attempt.success = True
        await self.session.commit()
        return attempt
