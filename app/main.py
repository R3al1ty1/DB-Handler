import uvicorn

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from contextlib import asynccontextmanager

from core.settings import settings
from handler.inserter import generate_collections
# from core.models.db_helper import db_helper

from api.api_v1.tables import router as table_router
from api.api_v1.databases import router as db_router
from api.api_v1.environments import router as env_router
from api.api_v1.fields import router as field_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Приложение запускается...")
    generate_collections()
    yield
    print("🛑 Приложение выключается...")

app = FastAPI(
    default_response_class=ORJSONResponse,
    lifespan=lifespan
)

app.include_router(
    env_router,
    prefix=settings.api.prefix,
)



app.include_router(
    db_router,
    prefix=settings.api.prefix,
)

app.include_router(
    field_router,
    prefix=settings.api.prefix,
)

app.include_router(
    table_router,
    prefix=settings.api.prefix,
)

if __name__=="__main__":
    uvicorn.run(
        "main:app",
        host=settings.run.host,
        port=settings.run.port,
        reload=True
    )