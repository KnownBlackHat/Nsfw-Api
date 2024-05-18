import random
from datetime import datetime
from typing import Dict, Generator, List, Set

import httpx
from aiocache import cached
from selectolax.parser import HTMLParser


class AdultScrapper:
    """
    Scraps Adult Content from Xnxx and Xvideos
    """

    def __init__(self, base_url: str, session: httpx.AsyncClient) -> None:
        self.session = session
        self.base_url = base_url

    @cached(ttl=60 * 60 * 12)
    async def _get_html(self, url: str) -> HTMLParser:
        resp = await self.session.get(url, headers={"User-Agent": "Magic Browser"})
        return HTMLParser(resp.text)

    @cached(ttl=60 * 60 * 12)
    async def extract_videos(self, url: str) -> Dict:
        """
        Extracts Video Data from Xnxx and Xvideos

        Parameters
        ----------
        url: Url of the video
        """
        dom = await self._get_html(url=url)
        data = dom.css_first('script[type="application/ld+json"]').text()
        data = dict(eval(data))
        parsed_date = datetime.strptime(
            data.get("uploadDate", "0000-00-00T00:00:00+00:00"), "%Y-%m-%dT%H:%M:%S%z"
        )
        payload = {
            "thumbnail": data.get("thumbnailUrl", [])[0],
            "upload_date": parsed_date.strftime("%Y-%m-%d %H:%M:%S"),
            "name": data.get("name"),
            "description": data.get("description", "").strip(),
            "content_url": data.get("contentUrl"),
        }
        return payload

    async def get_link(self, search: str, amount: int, xvideos: bool) -> Set[str]:
        """
        Gets the link of the video

        Parameters
        ----------
        search: What to search?
        xvideos: Search on xvideos or xnxx?
        """
        search_payload = (
            f"https://www.xvideos.com/?k={search}&top"
            if xvideos
            else f"https://www.xnxx.com/search/{search}?top"
        )
        dom = await self._get_html(url=search_payload)
        dom = dom.css_first("div.mozaique.cust-nb-cols").css("div.thumb")
        random.shuffle(dom)
        data: Generator = (
            f'{self.base_url}{link.css_first("a").attrs.get("href")}' for link in dom
        )
        return {next(data) for _ in range(amount)}

    async def send_video(self, search: str, amount: int, xvideos: bool = False) -> List:
        """
        Sends the video

        Parameters
        ----------
        search: What to search?
        amount: How much?
        xvideos: Search on xvideos or xnxx?
        """
        links = await self.get_link(search=search, amount=amount, xvideos=xvideos)
        return [await self.extract_videos(url=link) for link in links]

    async def get_redtube_video(self, amount: int, search: str) -> List:
        """
        Get Redtube Video

        Parameters
        ----------
        amount: How much?
        search: What to search?
        """
        resp = await self.session.get(
            "https://api.redtube.com/?"
            "data=redtube.Videos.searchVideos&"
            f"output=json&search={search}&"
            "thumbsize=all&page=1&sort=new"
        )
        data = resp.json()
        return random.choices(data["videos"], k=amount)
