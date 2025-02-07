from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from missionpanel.orm import Base, Mission, Tag, MissionTag, Matcher, Attempt

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
            Matcher(name="Ex hard"),
            Matcher(name="Ex Hard"),
            Matcher(name="Ex hard mission"),
            Matcher(name="Ex Hard Mission"),
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
            Matcher(name="Hard"),
            Matcher(name="Hard mission"),
            Matcher(name="Hard Mission"),
        ],
        tags=[
            MissionTag(tag=hdtag)
        ]
    )
    esmission = Mission(content="Easy")
    session.add_all([exmission, hdmission, esmission])
    session.commit()
