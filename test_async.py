import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from missionpanel.orm import Base, Mission, Tag, MissionTag, Matcher, Attempt
from missionpanel.submitter import AsyncSubmitter
from missionpanel.handler import AsyncHandler


class FakeHandler(AsyncHandler):
    async def select_mission(self, missions):
        return missions[0] if missions else None

    async def execute_mission(self, mission, attempt):
        print(f"Attempt {attempt.id} is executing mission {mission.content['name']}")
        return True


async def main(session: AsyncSession):
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
    await session.commit()

    submitter = AsyncSubmitter(session)
    await submitter.create_mission(content={"name": "Easy mission"}, match_patterns=["Easy mission", "Easy Mission", "E Mission"])
    await submitter.create_mission(content={"name": "Hard mission"}, match_patterns=["Hard mission", "Hard Mission", "H Mission"])
    await submitter.create_mission(content={"name": "Ex Hard mission"}, match_patterns=["Ex Hard mission", "Ex Hard Mission", "EX Mission"])
    await submitter.add_tags(["Easy mission"], ["Mission", "mission"])
    await submitter.add_tags(["Hard mission"], ["Mission", "mission"])
    await submitter.add_tags(["Ex Hard mission"], ["Mission", "mission"])

    # test handler

    handler = FakeHandler(session, "Ex hard handler")
    await handler.run_once(["Mission", "mission"])
    await handler.run_once(["Mission", "mission"])
    await handler.run_once(["Mission", "mission"])


async def async_main(engine: AsyncEngine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine) as session:
        await main(session)

if __name__ == "__main__":
    engine = create_async_engine("sqlite+aiosqlite://", echo=True)
    asyncio.run(async_main(engine))
