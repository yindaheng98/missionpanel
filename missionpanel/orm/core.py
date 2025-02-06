import datetime
from sqlalchemy import (
    Column,
    Integer,
    Text,
    JSON,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import relationship, DeclarativeBase


class Base(DeclarativeBase):
    pass


class Mission(Base):
    __tablename__ = "mission"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="Mission ID")
    content = Column(JSON, default={}, comment="Mission Content")
    create_time = Column(DateTime, default=datetime.datetime.now, comment="Mission Create Time")
    last_update_time = Column(DateTime, onupdate=datetime.datetime.now, comment="Mission Update Time")


class Tag(Base):
    __tablename__ = "tag"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="Tag ID")
    name = Column(Text, index=True, unique=True, comment="Tag Name")


class MissionTag(Base):
    __tablename__ = "missiontag"
    tag_id = Column(Integer, ForeignKey("tag.id"), primary_key=True, comment="Tag ID")
    match_mission = relationship("Tag", backref="tag_id")
    mission_id = Column(Integer, ForeignKey("mission.id"), primary_key=True, comment="Mission ID")
    match_mission = relationship("Mission", backref="tag_mission_id")


class Matcher(Base):
    __tablename__ = "matcher"
    name = Column(Text, primary_key=True, comment="Matcher Content")
    mission_id = Column(Integer, ForeignKey("mission.id"), index=True, comment="Mission ID")
    match_mission = relationship("Mission", backref="match_mission")
