import abc
from typing import AsyncGenerator, List, Any
import httpx
import logging
from xml.etree import ElementTree
from missionpanel.submitter import AsyncSubmitter


class RSSHubSubmitter(AsyncSubmitter, metaclass=abc.ABCMeta):
    logger = logging.getLogger("RSSHubSubmitter")

    @abc.abstractmethod
    async def parse_xml(self, xml: str) -> AsyncGenerator[dict, Any]:
        pass

    async def derive_tags(self, mission_content) -> List[str]:
        return ['rsshub']

    async def derive_matcher(self, mission_content) -> List[str]:
        return [mission_content['url']]

    async def create_missions(self, rsshub: str, **httpx_client_options):
        async with httpx.AsyncClient(**httpx_client_options) as client:
            response = await client.get(rsshub)
            async for mission_content in self.parse_xml(response.text):
                try:
                    matchers = await self.derive_matcher(mission_content)
                    await self.create_mission(mission_content, matchers)
                    tags = await self.derive_tags(mission_content)
                    if len(tags) > 0:
                        await self.add_tags(matchers, tags)
                except Exception as e:
                    self.logger.warning(f'create mission failed, error: {e}')


class RSSHubRootSubmitter(RSSHubSubmitter):

    async def parse_xml(self, xml: str) -> AsyncGenerator[dict, Any]:
        root = ElementTree.XML(xml)
        yield {
            'url': root.find('channel/link').text,
            'latest': [item.find('link').text for item in root.iter('item')][0]
        }


class RSSHubSubitemSubmitter(RSSHubSubmitter):

    async def parse_xml(self, xml: str) -> AsyncGenerator[dict, Any]:
        root = ElementTree.XML(xml)
        for item in root.find('channel').iter('item'):
            yield {'url': item.find('link').text}
