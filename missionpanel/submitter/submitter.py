from typing import List, Union, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from missionpanel.orm import Mission, Tag, Matcher, MissionTag
from sqlalchemy import Sequence, select, Select


class SubmitterInterface:
    @staticmethod
    def query_matcher(match_patterns: List[str]) -> Select[Tuple[Matcher]]:
        return select(Matcher).where(Matcher.pattern.in_(match_patterns)).limit(1).with_for_update()

    @staticmethod
    def add_mission_matchers(session: Union[Session | AsyncSession], match_patterns: List[str], existing_matcher: Union[Matcher | None] = None) -> Mission:
        if not existing_matcher:
            return
        exist_patterns = [matcher.pattern for matcher in existing_matcher.mission.matchers]
        session.add_all([Matcher(pattern=pattern, mission=existing_matcher.mission) for pattern in match_patterns if pattern not in exist_patterns])
        return existing_matcher.mission

    @staticmethod
    def create_mission(session: Session, content: str, match_patterns: List[str], existing_mission: Union[Mission | None] = None) -> Mission:
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
    def add_mission_tags(session: Session, mission: Mission, tags_name: List[str], exist_tags: Sequence[Tag] = []):
        exist_tags_name = [tag.name for tag in exist_tags]
        tags = [Tag(name=tag_name) for tag_name in tags_name if tag_name not in exist_tags_name]
        session.add_all(tags)
        exist_mission_tags = {mission_tag.tag_name: mission_tag.tag for mission_tag in mission.tags}
        session.add_all([MissionTag(mission=mission, tag_name=tag_name) for tag_name in tags_name if tag_name not in exist_mission_tags])
        return tags


class Submitter(SubmitterInterface):
    def __init__(self, session: Session):
        self.session = session

    def query_mission(self, match_patterns: List[str]) -> Mission:
        matcher = self.session.execute(SubmitterInterface.query_matcher(match_patterns)).scalars().first()
        mission = SubmitterInterface.add_mission_matchers(self.session, match_patterns, matcher)
        return mission

    def match_mission(self, match_patterns: List[str]) -> Mission:
        mission = self.query_mission(match_patterns)
        self.session.commit()
        return mission

    def _add_tags(self, mission: Union[Mission | None] = None, tags: List[str] = []):
        if mission is None and len(tags) > 0:
            raise ValueError("Mission not found")
        if len(tags) == 0:
            return []
        exist_tags = self.session.execute(SubmitterInterface.query_tag(tags)).scalars().all()
        tags = SubmitterInterface.add_mission_tags(self.session, mission, tags, exist_tags)
        return tags

    def create_mission(self, content: str, match_patterns: List[str], tags: List[str] = []):
        mission = self.query_mission(match_patterns)
        mission = SubmitterInterface.create_mission(self.session, content, match_patterns, mission)
        self._add_tags(mission, tags)
        self.session.commit()
        return mission

    def add_tags(self, match_patterns: List[str], tags: List[str]):
        mission = self.query_mission(match_patterns)
        tags = self._add_tags(mission, tags)
        self.session.commit()
        return tags


class AsyncSubmitter(SubmitterInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def match_mission(self, match_patterns: List[str]) -> Mission:
        async with self.session.begin():
            mission = SubmitterInterface.match_mission(self.session, match_patterns)
        await self.session.commit()
        return mission

    async def create_mission(self, content: str, match_patterns: List[str]):
        async with self.session.begin():
            mission = SubmitterInterface.create_mission(self.session, content, match_patterns)
        await self.session.commit()
        return mission

    async def add_tags(self, matchers: List[str], tags: List[str]):
        async with self.session.begin():
            tags = SubmitterInterface.add_tags(self.session, matchers, tags)
        await self.session.commit()
        return tags
