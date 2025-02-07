from typing import List
from sqlalchemy import or_
from sqlalchemy.orm import Session
from missionpanel.orm import Mission, Tag, Matcher, MissionTag


class Submitter:
    def __init__(self, session: Session):
        self.session = session

    def match_mission(self, match_patterns: List[str]) -> Mission:
        matcher = self.session.query(Matcher).filter(or_(Matcher.pattern == pattern for pattern in match_patterns)).with_for_update().first()
        if matcher:
            exist_patterns = [matcher.pattern for matcher in matcher.mission.matchers]
            self.session.add_all([Matcher(pattern=pattern, mission=matcher.mission) for pattern in match_patterns if pattern not in exist_patterns])
            self.session.commit()
            return matcher.mission

    def create_mission(self, content: str, match_patterns: List[str]):
        mission = self.match_mission(match_patterns)
        if mission is None:
            self.session.add(Mission(
                content=content,
                matchers=[Matcher(pattern=pattern) for pattern in match_patterns],
            ))
        else:
            if mission.content != content:
                mission.content = content
        self.session.commit()

    def _add_tags(self, mission: Mission, tags_name: List[str]):
        exist_tags = self.session.query(Tag).filter(or_(Tag.name == tag_name for tag_name in tags_name)).with_for_update().all()
        exist_tags_name = [tag.name for tag in exist_tags]
        self.session.add_all([Tag(name=tag_name) for tag_name in tags_name if tag_name not in exist_tags_name])
        exist_mission_tags = {mission_tag.tag_name: mission_tag.tag for mission_tag in mission.tags}
        self.session.add_all([MissionTag(mission=mission, tag_name=tag_name) for tag_name in tags_name if tag_name not in exist_mission_tags])
        self.session.commit()

    def add_tags(self, matchers: List[str], tags: List[str]):
        self._add_tags(self.match_mission(matchers), tags)
