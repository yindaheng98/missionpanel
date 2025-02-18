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
from sqlalchemy.ext.asyncio import AsyncAttrs


class Base(AsyncAttrs, DeclarativeBase):
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

    def __repr__(self):
        return f"Mission(id={self.id}, content={self.content.__repr__()}, create_time={self.create_time.__repr__()}, last_update_time={self.last_update_time.__repr__()})"


class Matcher(Base):
    __tablename__ = "matcher"
    pattern = Column(Text, primary_key=True, comment="Matcher Content")

    # relationship
    mission_id = Column(Integer, ForeignKey("mission.id"), index=True, comment="Mission ID")
    mission: Mapped['Mission'] = relationship(Mission, back_populates="matchers")

    def __repr__(self):
        return f"Matcher(pattern={self.pattern.__repr__()}, mission_id={self.mission_id})"


class Tag(Base):
    __tablename__ = "tag"
    name = Column(Text, primary_key=True, comment="Tag Name")

    # back populate relationships
    missions: Mapped[List['MissionTag']] = relationship(back_populates="tag")

    def __repr__(self):
        return f"Tag(name={self.name.__repr__()})"


class MissionTag(Base):
    __tablename__ = "missiontag"

    # relationship
    tag_name = Column(Text, ForeignKey("tag.name"), primary_key=True, comment="Tag")
    tag: Mapped['Tag'] = relationship(Tag, back_populates="missions")

    # relationship
    mission_id = Column(Integer, ForeignKey("mission.id"), primary_key=True, comment="Mission ID")
    mission: Mapped['Mission'] = relationship(Mission, back_populates="tags")

    def __repr__(self):
        return f"MissionTag(tag_name={self.tag_name.__repr__()}, mission_id={self.mission_id})"
