from typing import List

import httpx
from fastapi import APIRouter

from app.adultscrapper import AdultScrapper
from app.helper import elapsed_time, format_video_payload

router = APIRouter()


@router.get("/xnxx/{amount}/{search}")
@elapsed_time
async def xnxx(amount: int, search: str) -> List:
    """Get Xnxx Videos"""
    xnxx = AdultScrapper(base_url="https://www.xnxx.com", session=httpx.AsyncClient())
    links = await xnxx.send_video(search, amount)
    return [format_video_payload(vid) for vid in links]


@router.get("/xvideos/{amount}/{search}")
@elapsed_time
async def xvideos(amount: int, search: str) -> List:
    """Get Xvideos Videos"""
    xvideos = AdultScrapper(
        base_url="https://www.xvideos.com", session=httpx.AsyncClient()
    )
    links = await xvideos.send_video(search, amount, True)
    return [format_video_payload(vid) for vid in links]


@router.get("/redtube/{amount}/{search}")
@elapsed_time
async def redtube(amount: int, search: str) -> List:
    """Get Redtube Videos"""
    redtube = AdultScrapper(
        base_url="https://www.redtube.com", session=httpx.AsyncClient()
    )
    links = await redtube.get_redtube_video(amount, search)
    return [format_video_payload(vid.get("video"), True) for vid in links]
