from typing import List, Union
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from missionpanel.orm import Mission, MissionTag
from sqlalchemy import select
from .abc import SubmitterInterface


class AsyncSubmitterInterface(SubmitterInterface):

    @staticmethod
    async def _query_mission(session: AsyncSession, match_patterns: List[str]) -> Mission:
        matcher = (await session.execute(SubmitterInterface.query_matcher(match_patterns))).scalars().first()
        if matcher is None:
            return None
        mission = (await session.execute(select(Mission).where(Mission.id == matcher.mission_id).options(selectinload(Mission.matchers)))).scalars().first()
        SubmitterInterface.add_mission_matchers(session, mission, match_patterns, mission.matchers)
        return mission

    @staticmethod
    async def _add_tags(session: AsyncSession, mission: Union[Mission | None] = None, tags: List[str] = []):
        exist_tags = (await session.execute(SubmitterInterface.query_tag(tags))).scalars().all() if len(tags) > 0 else []
        exist_mission_tags = (await session.execute(select(MissionTag).where(MissionTag.mission_id == mission.id))).scalars().all()
        tags = SubmitterInterface.add_mission_tags(session, mission, tags, exist_tags, exist_mission_tags)
        return tags

    @staticmethod
    async def match_mission(session: AsyncSession, match_patterns: List[str]) -> Mission:
        mission = await AsyncSubmitterInterface._query_mission(session, match_patterns)
        await session.commit()
        return mission

    @staticmethod
    async def create_mission(session: AsyncSession, content: str, match_patterns: List[str], tags: List[str] = []):
        mission = await AsyncSubmitterInterface._query_mission(session, match_patterns)
        mission = SubmitterInterface.create_mission(session, content, match_patterns, mission)
        await AsyncSubmitterInterface._add_tags(session, mission, tags)
        await session.commit()
        return mission

    @staticmethod
    async def add_tags(session: AsyncSession, match_patterns: List[str], tags: List[str]):
        mission = await AsyncSubmitterInterface._query_mission(session, match_patterns)
        if mission is None:
            raise ValueError("Mission not found")
        tags = await AsyncSubmitterInterface._add_tags(session, mission, tags)
        await session.commit()
        return tags


class AsyncSubmitter(AsyncSubmitterInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def match_mission(self, match_patterns: List[str]) -> Mission:
        return await AsyncSubmitterInterface.match_mission(self.session, match_patterns)

    async def create_mission(self, content: str, match_patterns: List[str]):
        return await AsyncSubmitterInterface.create_mission(self.session, content, match_patterns)

    async def add_tags(self, matchers: List[str], tags: List[str]):
        return await AsyncSubmitterInterface.add_tags(self.session, matchers, tags)
