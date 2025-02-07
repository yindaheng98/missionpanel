import datetime
from typing import List
from sqlalchemy import (
    Column,
    Integer,
    Text,
    JSON,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped


class Base(DeclarativeBase):
    pass


class Mission(Base):
    __tablename__ = "mission"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="Mission ID")
    content = Column(JSON, default={}, comment="Mission Content")
    create_time = Column(DateTime, default=datetime.datetime.now, comment="Mission Create Time")
    last_update_time = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now, comment="Mission Update Time")

    # back populate relationships
    matchers: Mapped[List['Matcher']] = relationship(back_populates="mission")
    tags: Mapped[List['MissionTag']] = relationship(back_populates="mission")


class Matcher(Base):
    __tablename__ = "matcher"
    name = Column(Text, primary_key=True, comment="Matcher Content")

    # relationship
    mission_id = Column(Integer, ForeignKey("mission.id"), index=True, comment="Mission ID")
    mission: Mapped['Mission'] = relationship(Mission, back_populates="matchers")


class Tag(Base):
    __tablename__ = "tag"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="Tag ID")
    name = Column(Text, index=True, unique=True, comment="Tag Name")

    # back populate relationships
    missions: Mapped[List['MissionTag']] = relationship(back_populates="tag")


class MissionTag(Base):
    __tablename__ = "missiontag"

    # relationship
    tag_id = Column(Integer, ForeignKey("tag.id"), primary_key=True, comment="Tag ID")
    tag: Mapped['Tag'] = relationship(Tag, back_populates="missions")

    # relationship
    mission_id = Column(Integer, ForeignKey("mission.id"), primary_key=True, comment="Mission ID")
    mission: Mapped['Mission'] = relationship(Mission, back_populates="tags")
