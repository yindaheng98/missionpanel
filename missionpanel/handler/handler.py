import abc
import datetime
from typing import List, Optional
from sqlalchemy.orm import Session, Query
from missionpanel.orm import Mission, Tag, MissionTag, Attempt
from sqlalchemy import func, distinct, case


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

    def query_todo_missions(self, tags: List[str]) -> Query[Mission]:
        return (
            self.query_missions_by_tag(tags)
            .outerjoin(Attempt)
            .group_by(Mission.id)
            .having(func.count(
                case(((  # see if Attempt is finished or working on the Mission
                    Attempt.success.is_(True) |  # have finished handler
                    (Attempt.last_update_time + Attempt.max_time_interval >= datetime.datetime.now())  # have working handler
                ), 0), else_=None)) <= 0)  # get those Missions that have no finished or working Attempt
        )

    def run_once(self, tags: List[str]):
        missions = self.query_todo_missions(tags).all()
        mission = self.select_mission(missions)
        if mission is None:
            return
        attempt = Attempt(
            handler=self.name,
            max_time_interval=self.max_time_interval,
            content=mission.content,
            mission=mission)
        self.session.add(attempt)
        self.session.commit()
        if self.execute_mission(mission, attempt):
            attempt.success = True
            self.session.commit()
