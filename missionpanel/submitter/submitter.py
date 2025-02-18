from typing import List, Union, Tuple
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from missionpanel.orm import Mission, Tag, Matcher, MissionTag
from sqlalchemy import select, Select


class SubmitterInterface:
    @staticmethod
    def query_matcher(match_patterns: List[str]) -> Select[Tuple[Matcher]]:
        return select(Matcher).where(Matcher.pattern.in_(match_patterns)).limit(1).with_for_update()

    @staticmethod
    def add_mission_matchers(session: Union[Session | AsyncSession], mission: Mission, match_patterns: List[str], existing_matchers: List[Matcher] = []) -> Mission:
        exist_patterns = [matcher.pattern for matcher in existing_matchers]
        session.add_all([Matcher(pattern=pattern, mission=mission) for pattern in match_patterns if pattern not in exist_patterns])

    @staticmethod
    def create_mission(session: Union[Session | AsyncSession], content: str, match_patterns: List[str], existing_mission: Union[Mission | None] = None) -> Mission:
        mission = existing_mission
        if mission is None:
            mission = Mission(
                content=content,
                matchers=[Matcher(pattern=pattern) for pattern in match_patterns],
            )
            session.add(mission)
        else:
            if mission.content != content:
                mission.content = content
        return mission

    @staticmethod
    def query_tag(tags_name: List[str]) -> Select[Tuple[Matcher]]:
        return select(Tag).where(Tag.name.in_(tags_name)).with_for_update()

    @staticmethod
    def add_mission_tags(session: Union[Session | AsyncSession], mission: Mission, tags_name: List[str], exist_tags: List[Tag] = [], exist_mission_tags: List[Tag] = []):
        exist_tags_name = [tag.name for tag in exist_tags]
        session.add_all([Tag(name=tag_name) for tag_name in tags_name if tag_name not in exist_tags_name])
        exist_mission_tags_name = [tag.name for tag in exist_mission_tags]
        session.add_all([MissionTag(mission=mission, tag_name=tag_name) for tag_name in tags_name if tag_name not in exist_mission_tags_name])


class SyncSubmitterInterface(SubmitterInterface):

    @staticmethod
    def _query_mission(session: Session, match_patterns: List[str]) -> Mission:
        matcher = session.execute(SubmitterInterface.query_matcher(match_patterns)).scalars().first()
        if matcher is None:
            return None
        SubmitterInterface.add_mission_matchers(session, matcher.mission, match_patterns, matcher.mission.matchers)
        return matcher.mission

    @staticmethod
    def _add_tags(session: Session, mission: Union[Mission | None] = None, tags: List[str] = []):
        exist_tags = session.execute(SubmitterInterface.query_tag(tags)).scalars().all()
        exist_mission_tags = [mission_tag.tag for mission_tag in mission.tags]
        tags = SubmitterInterface.add_mission_tags(session, mission, tags, exist_tags, exist_mission_tags)
        return tags

    @staticmethod
    def match_mission(session: Session, match_patterns: List[str]) -> Mission:
        mission = SyncSubmitterInterface._query_mission(session, match_patterns)
        session.commit()
        return mission

    @staticmethod
    def create_mission(session: Session, content: str, match_patterns: List[str], tags: List[str] = []):
        mission = SyncSubmitterInterface._query_mission(session, match_patterns)
        mission = SubmitterInterface.create_mission(session, content, match_patterns, mission)
        SyncSubmitterInterface._add_tags(session, mission, tags)
        session.commit()
        return mission

    @staticmethod
    def add_tags(session: Session, match_patterns: List[str], tags: List[str]):
        mission = SyncSubmitterInterface._query_mission(session, match_patterns)
        if mission is None:
            raise ValueError("Mission not found")
        tags = SyncSubmitterInterface._add_tags(session, mission, tags)
        session.commit()
        return tags


class Submitter(SyncSubmitterInterface):
    def __init__(self, session: Session):
        self.session = session

    def match_mission(self, match_patterns: List[str]) -> Mission:
        return SyncSubmitterInterface.match_mission(self.session, match_patterns)

    def create_mission(self, content: str, match_patterns: List[str], tags: List[str] = []):
        return SyncSubmitterInterface.create_mission(self.session, content, match_patterns, tags)

    def add_tags(self, match_patterns: List[str], tags: List[str]):
        return SyncSubmitterInterface.add_tags(self.session, match_patterns, tags)


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
        exist_mission_tags = (await session.execute(select(Tag).join(MissionTag).filter(MissionTag.mission_id == mission.id))).scalars().all()
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
    async def add_tags(session: Session, match_patterns: List[str], tags: List[str]):
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
