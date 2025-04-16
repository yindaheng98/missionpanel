import asyncio
import logging
from typing import List
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from missionpanel.orm import Base
from missionpanel.example import RSSHubRootSubmitter, RSSHubSubitemSubmitter
from missionpanel.example import TTRSSHubRootSubmitter, SubprocessAsyncHandlerInterface
from missionpanel.handler import AsyncHandler, ParallelAsyncHandler
from missionpanel.orm import Mission, Attempt

logging.basicConfig(level=logging.INFO)


class FakeHandlerInterface(SubprocessAsyncHandlerInterface):

    async def select_mission(self, missions):
        return missions[0] if missions else None

    async def construct_command(self, mission: Mission, attempt: Attempt) -> List[str]:
        return ["D:/MyPrograms/gallery-dl.exe", mission.content['url']]


class FakeHandler(FakeHandlerInterface, ParallelAsyncHandler):
    pass


class TagRSSHubSubitemSubmitter(RSSHubSubitemSubmitter):
    def __init__(self, session, tags=[]):
        super().__init__(session)
        self.tags = tags

    async def derive_tags(self, mission_content):
        return self.tags


async def main(session: AsyncSession):
    submitter = RSSHubRootSubmitter(session)
    await submitter.create_missions(rsshub="https://rsshub.app/twitter/user/diygod")
    sub_submitter = TagRSSHubSubitemSubmitter(session, ['twitter'])
    await sub_submitter.create_missions(rsshub="https://rsshub.app/youtube/user/@JFlaMusic")
    submitter = TTRRSSHubRootSubmitter(session)
    await submitter.create_missions(
        url='http://localhost/api/',
        username='admin',
        password='123456',
        cat_id=0,
    )
    handler = FakeHandler(session, 'example handler')
    await handler.run_all(['twitter'])


async def async_main(engine: AsyncEngine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine) as session:
        await main(session)

if __name__ == "__main__":
    engine = create_async_engine("sqlite+aiosqlite:///data.db", echo=True)
    asyncio.run(async_main(engine))
