from fastapi import APIRouter

from api.api_v1.tables import router as table_router
from api.api_v1.databases import router as db_router
from api.api_v1.environments import router as env_router
from api.api_v1.fields import router as field_router


router = APIRouter()


router.include_router(
    env_router
)

router.include_router(
    db_router
)

router.include_router(
    table_router
)

router.include_router(
    field_router
)
