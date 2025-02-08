from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from missionpanel.orm import Base, Mission, Tag, MissionTag, Matcher, Attempt
from missionpanel.submitter import Submitter
from missionpanel.handler import Handler


class FakeHandler(Handler):
    def select_mission(self, missions):
        return missions[0] if missions else None

    def execute_mission(self, mission, attempt):
        return True


engine = create_engine("sqlite://", echo=True)
Base.metadata.create_all(engine)

with Session(engine) as session:
    extag = Tag(
        name="ex hard"
    )
    hdtag = Tag(
        name="hard"
    )
    session.add_all([extag, hdtag])
    exmission = Mission(
        content="Ex hard mission",
        matchers=[
            Matcher(pattern="Ex hard"),
            Matcher(pattern="Ex Hard"),
            Matcher(pattern="Ex hard mission"),
            Matcher(pattern="Ex Hard Mission"),
        ],
        tags=[
            MissionTag(tag=extag),
            MissionTag(tag=hdtag)
        ],
        attempts=[
            Attempt(handler='Ex hard handler')
        ]
    )
    hdmission = Mission(
        content="Hard mission",
        matchers=[
            Matcher(pattern="Hard"),
            Matcher(pattern="Hard mission"),
            Matcher(pattern="Hard Mission"),
        ],
        tags=[
            MissionTag(tag=hdtag)
        ]
    )
    esmission = Mission(content="Easy mission")
    session.add_all([exmission, hdmission, esmission])
    session.commit()

    submitter = Submitter(session)
    submitter.create_mission(content="Easy mission", match_patterns=["Easy mission", "Easy Mission", "E Mission"])
    submitter.create_mission(content="Hard mission", match_patterns=["Hard mission", "Hard Mission", "H Mission"])
    submitter.create_mission(content="Ex Hard mission", match_patterns=["Ex Hard mission", "Ex Hard Mission", "EX Mission"])
    submitter.add_tags(["Easy mission"], ["Mission", "mission"])
    submitter.add_tags(["Hard mission"], ["Mission", "mission"])
    submitter.add_tags(["Easy mission"], ["Mission", "mission"])

    handler = FakeHandler(session, "Ex hard handler")
    missions = handler.query_missions_by_tag(["Mission", "mission"])
    print(missions.all())
