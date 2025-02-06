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
    last_update_time = Column(DateTime, onupdate=datetime.datetime.now, comment="Mission Update Time")


class Tag(Base):
    __tablename__ = "tag"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="Tag ID")
    name = Column(Text, index=True, unique=True, comment="Tag Name")


class MissionTag(Base):
    __tablename__ = "missiontag"

    # relationship
    tag_id = Column(Integer, ForeignKey("tag.id"), primary_key=True, comment="Tag ID")
    tag: Mapped['Tag'] = relationship(backref="missions")

    # relationship
    mission_id = Column(Integer, ForeignKey("mission.id"), primary_key=True, comment="Mission ID")
    mission: Mapped['Mission'] = relationship(backref="tags")


class Matcher(Base):
    __tablename__ = "matcher"
    name = Column(Text, primary_key=True, comment="Matcher Content")

    # relationship
    mission_id = Column(Integer, ForeignKey("mission.id"), index=True, comment="Mission ID")
    mission: Mapped['Mission'] = relationship(backref="matchers")


if __name__ == "__main__":
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    engine = create_engine("sqlite://", echo=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        exmission = Mission(
            content="Ex hard mission",
            matchers=[
                Matcher(name="Ex hard"),
                Matcher(name="Ex Hard"),
                Matcher(name="Ex hard mission"),
                Matcher(name="Ex Hard Mission"),
            ],
        )
        hdmission = Mission(
            content="Hard mission",
            matchers=[
                Matcher(name="Hard"),
                Matcher(name="Hard mission"),
                Matcher(name="Hard Mission"),
            ],
        )
        esmission = Mission(content="Easy")
        session.add_all([exmission, hdmission, esmission])
        session.commit()
