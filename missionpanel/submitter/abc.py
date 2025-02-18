from typing import List, Union, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from missionpanel.orm import Mission, Tag, Matcher, MissionTag
from sqlalchemy import select, Select


class SubmitterInterface:
    '''
    SubmitterInterface is an interface for Submitter and AsyncSubmitter to implement the common methods.
    There is no anything about session.execute in this class.
    '''
    @staticmethod
    def query_matcher(match_patterns: List[str]) -> Select[Tuple[Matcher]]:
        return select(Matcher).where(Matcher.pattern.in_(match_patterns)).limit(1).with_for_update()

    @staticmethod
    def add_mission_matchers(session: Union[Session | AsyncSession], mission: Mission, match_patterns: List[str], existing_matchers: List[Matcher] = []) -> Mission:
        exist_patterns = [matcher.pattern for matcher in existing_matchers]
        session.add_all([Matcher(pattern=pattern, mission=mission) for pattern in match_patterns if pattern not in exist_patterns])

    @staticmethod
    def create_mission(session: Union[Session | AsyncSession], content: str, match_patterns: List[str], existing_mission: Union[Mission | None] = None) -> Mission:
        if existing_mission is None:
            mission = Mission(
                content=content,
                matchers=[Matcher(pattern=pattern) for pattern in match_patterns],
            )
            session.add(mission)
        else:
            mission = existing_mission
            if mission.content != content:
                mission.content = content
        return mission

    @staticmethod
    def query_tag(tags_name: List[str]) -> Select[Tuple[Matcher]]:
        return select(Tag).where(Tag.name.in_(tags_name)).with_for_update()

    @staticmethod
    def add_mission_tags(session: Union[Session | AsyncSession], mission: Mission, tags_name: List[str], exist_tags: List[Tag] = [], exist_mission_tags: List[MissionTag] = []):
        exist_tags_name = [tag.name for tag in exist_tags]
        session.add_all([Tag(name=tag_name) for tag_name in tags_name if tag_name not in exist_tags_name])
        exist_mission_tags_name = [tag.tag_name for tag in exist_mission_tags]
        session.add_all([MissionTag(mission=mission, tag_name=tag_name) for tag_name in tags_name if tag_name not in exist_mission_tags_name])
