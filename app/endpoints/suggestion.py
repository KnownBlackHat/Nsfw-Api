from typing import List

import httpx
from aiocache import cached
from fastapi import APIRouter
from helper import elapsed_time

router = APIRouter()


@router.get("/suggestion/xvideos/{search}")
@elapsed_time
@cached(ttl=60 * 60 * 1)
async def xvideos_suggestion(search: str) -> List:
    async with httpx.AsyncClient() as client:
        data = await client.get(f"https://www.xvideos.com/search-suggest/{search}")
        return [keywords.get("N") for keywords in data.json().get("keywords", [])]


@router.get("/suggestion/xnxx/{search}")
@elapsed_time
@cached(ttl=60 * 60 * 1)
async def xnxx_suggestion(search: str) -> List:
    async with httpx.AsyncClient() as client:
        data = await client.get(f"https://www.xnxx.com/search-suggest/{search}")
        return [keywords.get("N") for keywords in data.json().get("keywords", [])]
