import abc
import asyncio
import json
import logging
import traceback
from typing import Any, AsyncGenerator, Dict, List, Union
import httpx
from xml.etree import ElementTree
from missionpanel.submitter import AsyncSubmitter


class TTRSSClient(httpx.AsyncClient):
    """一个简单的异步TTRSS客户端"""
    sem_list: Dict[str, asyncio.Semaphore] = {}  # 同一时刻一个链接只能有一个客户端登录，这里用一个信号量列表控制

    def __init__(self, url: str, username: str, password: str, **kwargs):
        super().__init__(**kwargs)
        self.__url = url
        self.__username = username
        self.__password = password
        self.__logger = logging.getLogger("TTRSSClient")
        self.__sid = None
        if self.__url not in TTRSSClient.sem_list:  # 给每个链接一个信号量
            TTRSSClient.sem_list[self.__url] = None  # 信号量必须在事件循环开始后生成，此处先给个标记

    async def __aenter__(self):
        for url in TTRSSClient.sem_list:  # 信号量必须在事件循环开始后生成
            if TTRSSClient.sem_list[url] is None:  # 已经生成的信号量不要变
                self.__logger.debug('semaphore for TTRSS API %s initialized' % url)
                TTRSSClient.sem_list[url] = asyncio.Semaphore(1)  # 生成信号量
        await TTRSSClient.sem_list[self.__url].__aenter__()  # 同一时刻一个链接只能有一个客户端登录
        self.__logger.debug('semaphore for TTRSS API %s got' % self.__url)
        await super().__aenter__()
        self.__logger.debug('httpx cli for TTRSS API %s initialized' % self.__url)
        try:
            data = (await super().post(self.__url, content=json.dumps({
                'op': 'login',
                'user': self.__username,
                'password': self.__password
            }))).json()
            self.__logger.debug('TTRSS API login response: %s' % data)
            self.__sid = data['content']['session_id']
            self.__logger.debug('TTRSS API login successful, sid: %s' % self.__sid)
        except Exception:
            self.__logger.exception('TTRSS API login failed, error: ')
        return self

    async def __aexit__(self, *args, **kwargs):
        try:
            data = (await super().post(self.__url, content=json.dumps({
                "sid": self.__sid,
                "op": "logout"
            }))).json()
            self.__logger.debug('TTRSS API logout response: %s' % data)
            self.__logger.debug('TTRSS API logout successful, sid: %s' % self.__sid)
        except Exception:
            self.__logger.exception('TTRSS API logout failed, error: ')
        await super().__aexit__(*args, **kwargs)
        await TTRSSClient.sem_list[self.__url].__aexit__(*args, **kwargs)
        self.__logger.debug('semaphore for TTRSS API %s released' % self.__url)

    async def api(self, data: dict):
        data['sid'] = self.__sid
        self.__logger.debug("post data to  TTRSS API %s: %s" % (self.__url, data))
        try:
            return (await super().post(self.__url, content=json.dumps(data))).json()['content']
        except Exception:
            self.__logger.exception('TTRSS API post failed, error: ')
            return None


class TTRSSSubmitter(AsyncSubmitter, metaclass=abc.ABCMeta):
    logger = logging.getLogger("TTRSSSubmitter")

    @abc.abstractmethod
    async def parse_content(self, feed: dict, content: dict) -> AsyncGenerator[dict, Any]:
        pass

    async def derive_tags(self, mission_content) -> List[str]:
        return ['ttrss']

    async def derive_matcher(self, mission_content) -> List[str]:
        return [mission_content['url']]

    async def create_missions(self, url: str, username: str, password: str, cat_id: int, semaphore=asyncio.Semaphore(3), **httpx_client_options):
        async with TTRSSClient(url, username, password, **httpx_client_options) as client:
            feeds = await client.api({
                "op": "getFeeds",
                "cat_id": cat_id,
                "limit": None
            })

            mission_content_queue = asyncio.Queue(len(feeds))

            async def feed_task(feed):
                async with semaphore:
                    content = await client.api({
                        "op": "getHeadlines",
                        "feed_id": feed['id'],
                        "limit": 1,
                        "view_mode": "all_articles",
                        "order_by": "feed_dates"
                    })
                    async for mission_content in self.parse_content(feed, content, **httpx_client_options):
                        await mission_content_queue.put(mission_content)

            async def mission_task():
                while True:
                    mission_content = await mission_content_queue.get()
                    try:
                        matchers = await self.derive_matcher(mission_content)
                        await self.create_mission(mission_content, matchers)
                        tags = await self.derive_tags(mission_content)
                        if len(tags) > 0:
                            await self.add_tags(matchers, tags)
                    except Exception as e:
                        self.logger.warning(f'create mission failed, error: {e}, traceback: {traceback.format_exc()}')
                    mission_content_queue.task_done()

            mission_task_ = asyncio.create_task(mission_task())
            await asyncio.gather(*[feed_task(feed) for feed in sorted(feeds, key=lambda feed: -feed['last_updated'])])  # wait for all feed tasks to finish
            await mission_content_queue.join()  # wait for all missions to be done
            mission_task_.cancel()  # cancel the while True in mission task


class TTRSSHubSubmitter(TTRSSSubmitter):
    logger = logging.getLogger("TTRSSHubSubmitter")

    @abc.abstractmethod
    async def parse_xml(self, xml: str, feed: dict, content: dict) -> AsyncGenerator[dict, Any]:
        pass

    async def preprocess(self, feed: dict, content: dict) -> Union[Dict, None]:
        return feed

    async def parse_content_nocatch(self, feed: dict, content: dict, **httpx_client_options) -> AsyncGenerator[dict, Any]:
        feed = await self.preprocess(feed, content)
        if feed is None:
            return
        async with httpx.AsyncClient(**httpx_client_options) as client:
            response = await client.get(feed['feed_url'])
            async for mission_content in self.parse_xml(response.text, feed, content):
                yield mission_content

    async def parse_content(self, feed: dict, content: dict, **httpx_client_options) -> AsyncGenerator[dict, Any]:
        try:
            async for mission_content in self.parse_content_nocatch(feed, content, **httpx_client_options):
                yield mission_content
        except Exception as e:
            self.logger.warning(f'parse content failed, error: {e}, traceback: {traceback.format_exc()}')


class TTRSSHubRootSubmitter(TTRSSHubSubmitter):

    async def parse_xml(self, xml: str, feed: dict, content: dict) -> AsyncGenerator[dict, Any]:
        root = ElementTree.XML(xml)
        yield {
            'url': root.find('channel/link').text,
            'latest': [item.find('link').text for item in root.iter('item')][0],
            'feed_url': feed['feed_url'],
        }


class TTRSSHubSubitemSubmitter(TTRSSHubSubmitter):

    async def parse_xml(self, xml: str, feed: dict, content: dict) -> AsyncGenerator[dict, Any]:
        root = ElementTree.XML(xml)
        for item in root.find('channel').iter('item'):
            yield {'url': item.find('link').text, 'feed_url': feed['feed_url']}
