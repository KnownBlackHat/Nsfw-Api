import logging
from functools import wraps
from time import time
from typing import Awaitable, Callable, Dict, List  # , ParamSpec

from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)
# P = ParamSpec("P")


def elapsed_time(
    func: Callable[
        ..., Awaitable[List]
    ]  # instead of P ellipse is being used for vercel py 3.9 runtime compatibility
) -> Callable[..., Awaitable[JSONResponse]]:
    """Decorator to calculate the elapsed time of the function"""

    @wraps(func)
    # async def wrapper(*args: P.args, **kwargs: P.kwargs) -> JSONResponse:
    async def wrapper(*args: object, **kwargs: object) -> JSONResponse:
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
