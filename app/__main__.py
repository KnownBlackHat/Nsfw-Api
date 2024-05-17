import logging

from fastapi import FastAPI

from app.endpoints.root import router as root
from app.endpoints.suggestion import router as suggestion_endpoint

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

if __name__ == "__main__":
    import os

    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
