import abc
import asyncio
import logging
import chardet
from typing import List, Callable
from missionpanel.handler import AsyncHandler
from missionpanel.orm.core import Mission
from missionpanel.orm.handler import Attempt


class SubprocessAsyncHandlerInterface(AsyncHandler, abc.ABC):
    def getLogger(self) -> logging.Logger:
        return logging.getLogger("SubprocessAsyncHandler")

    async def __readline_info(self, f):
        async for line in f:
            try:
                line = line.decode(chardet.detect(line)['encoding']).strip()
            except UnicodeDecodeError:
                line = line.strip()
            self.getLogger().info('stdout | %s' % line)

    async def __readline_debug(self, f):
        async for line in f:
            try:
                line = line.decode(chardet.detect(line)['encoding']).strip()
            except UnicodeDecodeError:
                line = line.strip()
            self.getLogger().info('stderr | %s' % line)

    @abc.abstractmethod
    async def construct_command(self, mission: Mission, attempt: Attempt) -> List[str]:
        raise NotImplementedError("Subclasses must implement construct_command")

    async def execute_mission(self, mission: Mission, attempt: Attempt) -> bool:
        proc = await asyncio.create_subprocess_exec(
            *(await self.construct_command(mission, attempt)),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        await asyncio.gather(self.__readline_info(proc.stdout), self.__readline_debug(proc.stderr))
        return (await proc.wait()) == 0
