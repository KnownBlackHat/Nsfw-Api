import logging
import random
from datetime import datetime
from functools import wraps
from time import time
from typing import Awaitable, Callable, Dict, Generator, List, Set, ParamSpec

import httpx
from aiocache import cached
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from selectolax.parser import HTMLParser


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
logging.getLogger("httpx").setLevel(logging.WARNING)


app = FastAPI(openapi_url="", redoc_url=None)


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



P = ParamSpec("P")
def elapsed_time(
    func: Callable[P, Awaitable[List]]
) -> Callable[P, Awaitable[JSONResponse]]:
    """Decorator to calculate the elapsed time of the function"""

    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> JSONResponse:
        start = time()
        result = await func(*args, **kwargs)
        end = time()
        total_time = end - start
        logger.info(
            f"Function {func.__name__}{args} {kwargs} Took {total_time:.4f} seconds"
        )
        alter_res = {"data": result, "elapsed_time": total_time}
        return JSONResponse(alter_res, 200)

    return wrapper


def format_video_payload(video: Dict, isredtube: bool = False) -> Dict:
    """Formats the video payload"""
    metadata = ["name", "description", "upload_date", "thumbnail", "content_url"]
    if isredtube:
        metadata = [
            "title",
            "url",
            "duration",
            "default_thumb",
        ]  # metadata key for redtube
    metainfo = dict.fromkeys(metadata, "")
    for key in metadata:
        metainfo[key] = video.get(key, "").strip()
    return metainfo


@app.get("/xnxx/{amount}/{search}")
@elapsed_time
async def xnxx(amount: int, search: str) -> List:
    """Get Xnxx Videos"""
    xnxx = AdultScrapper(base_url="https://www.xnxx.com", session=httpx.AsyncClient())
    links = await xnxx.send_video(search, amount)
    return [format_video_payload(vid) for vid in links]


@app.get("/xvideos/{amount}/{search}")
@elapsed_time
async def xvideos(amount: int, search: str) -> List:
    """Get Xvideos Videos"""
    xvideos = AdultScrapper(
        base_url="https://www.xvideos.com", session=httpx.AsyncClient()
    )
    links = await xvideos.send_video(search, amount, True)
    return [format_video_payload(vid) for vid in links]


@app.get("/redtube/{amount}/{search}")
@elapsed_time
async def redtube(amount: int, search: str) -> List:
    """Get Redtube Videos"""
    redtube = AdultScrapper(
        base_url="https://www.redtube.com", session=httpx.AsyncClient()
    )
    links = await redtube.get_redtube_video(amount, search)
    return [format_video_payload(vid.get("video"), True) for vid in links]


@app.get("/suggestion/xvideos/{search}")
@elapsed_time
@cached(ttl=60 * 60 * 1)
async def xvideos_suggestion(search: str) -> List:
    async with httpx.AsyncClient() as client:
        data = await client.get(f"https://www.xvideos.com/search-suggest/{search}")
        return [keywords.get("N") for keywords in data.json().get("keywords", [])]


@app.get("/suggestion/xnxx/{search}")
@elapsed_time
@cached(ttl=60 * 60 * 1)
async def xnxx_suggestion(search: str) -> List:
    async with httpx.AsyncClient() as client:
        data = await client.get(f"https://www.xnxx.com/search-suggest/{search}")
        return [keywords.get("N") for keywords in data.json().get("keywords", [])]
