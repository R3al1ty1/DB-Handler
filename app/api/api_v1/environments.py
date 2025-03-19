from fastapi import APIRouter, HTTPException
from typing import Dict, List

from core.settings import settings
from core.crud.environments import db_create_environment, db_delete_environment, db_get_environment_specific, db_get_environments
from core.schemas.environments import EnvironmentCreateRequest


db = settings.db.db_client

router = APIRouter(
    # prefix=settings.api.v1.prefix,
    tags=["Environments"]
)


@router.post("/environments/add", response_model=Dict)
async def create_environment(environment: EnvironmentCreateRequest):
    try:
        env_id = await db_create_environment(environment.name)
        if not env_id:
            raise HTTPException(status_code=400, detail="Область с таким названием уже существует")
        
        return {
            "environment_id": env_id,
            "message": f"Область '{environment.name}' успешно создана"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при создании области: {str(e)}")


@router.get("/environments", response_model=List)
async def get_environments():
    try:
        environments = await db_get_environments()
        if not environments:
            raise HTTPException(status_code=404, detail="Среды не найдены")

        return environments

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при извлечении данных: {str(e)}")


@router.get("/environments/{environment_id}", response_model=Dict)
async def get_databases_for_environment(environment_id: str):
    try:
        environment = await db_get_environment_specific(env_id=environment_id)
        if not environment:
            raise HTTPException(status_code=404, detail="Среда не найдена")

        return environment

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при извлечении данных: {str(e)}")


@router.delete("/environments/delete/{environment_id}")
async def delete_environment(environment_id: str):
    try:
        environment = await db_delete_environment(env_id=environment_id)
        if not environment:
            raise HTTPException(status_code=404, detail="Среда не найдена")

        return {"message": f"Среда с ID '{environment_id}' успешно удалена"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при извлечении данных: {str(e)}")
