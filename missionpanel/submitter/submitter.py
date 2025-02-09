from typing import List
from sqlalchemy.orm import Session
from missionpanel.orm import Mission, Tag, Matcher, MissionTag


class SubmitterInterface:
    @staticmethod
    def match_mission(session: Session, match_patterns: List[str]) -> Mission:
        matcher = session.query(Matcher).filter(Matcher.pattern.in_(match_patterns)).with_for_update().first()
        if matcher:
            exist_patterns = [matcher.pattern for matcher in matcher.mission.matchers]
            session.add_all([Matcher(pattern=pattern, mission=matcher.mission) for pattern in match_patterns if pattern not in exist_patterns])
            return matcher.mission

    @staticmethod
    def create_mission(session: Session, content: str, match_patterns: List[str]):
        mission = SubmitterInterface.match_mission(session, match_patterns)
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
    def _add_tags(session: Session, mission: Mission, tags_name: List[str]):
        exist_tags = session.query(Tag).filter(Tag.name.in_(tags_name)).with_for_update().all()
        exist_tags_name = [tag.name for tag in exist_tags]
        tags = [Tag(name=tag_name) for tag_name in tags_name if tag_name not in exist_tags_name]
        session.add_all(tags)
        exist_mission_tags = {mission_tag.tag_name: mission_tag.tag for mission_tag in mission.tags}
        session.add_all([MissionTag(mission=mission, tag_name=tag_name) for tag_name in tags_name if tag_name not in exist_mission_tags])
        return tags

    @staticmethod
    def add_tags(session: Session, matchers: List[str], tags: List[str]):
        SubmitterInterface._add_tags(session, SubmitterInterface.match_mission(session, matchers), tags)


class Submitter(SubmitterInterface):
    def __init__(self, session: Session):
        self.session = session

    def match_mission(self, match_patterns: List[str]) -> Mission:
        mission = SubmitterInterface.match_mission(self.session, match_patterns)
        self.session.commit()
        return mission

    def create_mission(self, content: str, match_patterns: List[str]):
        mission = SubmitterInterface.create_mission(self.session, content, match_patterns)
        self.session.commit()
        return mission

    def add_tags(self, matchers: List[str], tags: List[str]):
        tags = SubmitterInterface.add_tags(self.session, matchers, tags)
        self.session.commit()
        return tags
