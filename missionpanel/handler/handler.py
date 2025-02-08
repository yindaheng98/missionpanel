import abc
import datetime
from typing import List, Optional
from sqlalchemy.orm import Session, Query
from missionpanel.orm import Mission, Tag, MissionTag, Attempt
from sqlalchemy import func, distinct, or_, and_


class Handler(abc.ABC):
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

    def query_missions_by_tag(self, tags: List[str]) -> Query[Mission]:
        return (
            self.session.query(Mission)
            .join(MissionTag)
            .join(Tag)
            .filter(Tag.name.in_(tags))
            .group_by(Mission.id)
            .having(func.count(distinct(Tag.name)) == len(tags))
        )
