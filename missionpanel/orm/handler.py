import datetime
from sqlalchemy import (
    Column,
    Integer,
    Text,
    JSON,
    Boolean,
    DateTime,
    Interval,
    ForeignKey
)
from sqlalchemy.orm import relationship, Mapped
from .core import Base, Mission


class Attempt(Base):
    __tablename__ = "attempt"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="Mission ID")
    handler = Column(Text, comment="Handler Name")
    create_time = Column(DateTime, default=datetime.datetime.now, comment="Attempt Start Time")
    last_update_time = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, comment="Attempt Last Update Time")
    max_time_interval = Column(Interval, default=datetime.timedelta(seconds=1), comment="Attempt Update Time Interval")
    content = Column(JSON, default={}, comment="Mission Content at that time")
    success = Column(Boolean, default=False, comment="If this Attempt has succeed")

    # relationship
    mission_id = Column(Integer, ForeignKey("mission.id"), comment="Mission ID")
    mission: Mapped['Mission'] = relationship(Mission, backref="attempts")

    def __repr__(self):
        return f"Attempt(id={self.id}, handler={self.handler.__repr__()}, create_time={self.create_time.__repr__()}, last_update_time={self.last_update_time.__repr__()}, max_time_interval={self.max_time_interval.__repr__()}, content={self.content.__repr__()}, success={self.success}, mission_id={self.mission_id})"
