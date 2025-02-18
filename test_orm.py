from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from missionpanel.orm import Base, Mission, Tag, MissionTag, Matcher, Attempt
from missionpanel.submitter import Submitter
from missionpanel.handler import Handler


class FakeHandler(Handler):
    def select_mission(self, missions):
        return missions[0] if missions else None

    def execute_mission(self, mission, attempt):
        print(f"Attempt {attempt.id} is executing mission {mission.content['name']}")
        return True


def main(session: Session):
    extag = Tag(
        name="ex hard"
    )
    hdtag = Tag(
        name="hard"
    )
    session.add_all([extag, hdtag])
    exmission = Mission(
        content={"name": "Ex hard mission"},
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
        content={"name": "Hard mission"},
        matchers=[
            Matcher(pattern="Hard"),
            Matcher(pattern="Hard mission"),
            Matcher(pattern="Hard Mission"),
        ],
        tags=[
            MissionTag(tag=hdtag)
        ]
    )
    esmission = Mission(content={"name": "Easy mission"})
    session.add_all([exmission, hdmission, esmission])
    session.commit()

    submitter = Submitter(session)
    submitter.create_mission(content={"name": "Easy mission"}, match_patterns=["Easy mission", "Easy Mission", "E Mission"])
    submitter.create_mission(content={"name": "Hard mission"}, match_patterns=["Hard mission", "Hard Mission", "H Mission"])
    submitter.create_mission(content={"name": "Ex Hard mission"}, match_patterns=["Ex Hard mission", "Ex Hard Mission", "EX Mission"])
    submitter.add_tags(["Easy mission"], ["Mission", "mission"])
    submitter.add_tags(["Hard mission"], ["Mission", "mission"])
    submitter.add_tags(["Ex Hard mission"], ["Mission", "mission"])

    # test handler

    handler = FakeHandler(session, "Ex hard handler")
    handler.run_once(["Mission", "mission"])
    handler.run_once(["Mission", "mission"])
    handler.run_once(["Mission", "mission"])


if __name__ == "__main__":
    engine = create_engine("sqlite://", echo=True)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        main(session)
