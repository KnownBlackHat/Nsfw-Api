import logging

from endpoints.root import router as root
from endpoints.suggestion import router as suggestion_endpoint
from fastapi import FastAPI

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
logging.getLogger("httpx").setLevel(logging.WARNING)


app = FastAPI(openapi_url="", redoc_url=None)
app.include_router(root)
app.include_router(suggestion_endpoint)

from endpoints import root, suggestion
from fastapi import FastAPI

app = FastAPI()

app.include_router(root.router)
app.include_router(suggestion.router)
