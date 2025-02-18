from typing import List, Union
from sqlalchemy.orm import Session
from missionpanel.orm import Mission
from .abc import SubmitterInterface


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
        tags = SubmitterInterface.add_mission_tags(session, mission, tags, exist_tags, mission.tags)

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
        SyncSubmitterInterface._add_tags(session, mission, tags)
        session.commit()


class Submitter(SyncSubmitterInterface):
    def __init__(self, session: Session):
        self.session = session

    def match_mission(self, match_patterns: List[str]) -> Mission:
        return SyncSubmitterInterface.match_mission(self.session, match_patterns)

    def create_mission(self, content: str, match_patterns: List[str], tags: List[str] = []):
        return SyncSubmitterInterface.create_mission(self.session, content, match_patterns, tags)

    def add_tags(self, match_patterns: List[str], tags: List[str]):
        return SyncSubmitterInterface.add_tags(self.session, match_patterns, tags)
