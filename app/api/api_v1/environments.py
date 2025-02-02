from fastapi import APIRouter, HTTPException
from typing import Dict

from core.settings import settings
from core.schemas.handler import EnvironmentCreateRequest
from handler.inserter import upload_environment


db = settings.db.db_client

router = APIRouter(
    prefix=settings.api.v1.arango,
    tags=["Environments"]
)


@router.post("/environments/add", response_model=Dict)
async def create_environment(environment: EnvironmentCreateRequest):
    existing_environment = db.collection("environments").find({"name": environment.name})
    if existing_environment:
        raise HTTPException(status_code=400, detail="Область с таким названием уже существует")
    
    try:
        upload_environment(environment.name)
        
        return {"message": f"Область '{environment.name}' успешно создана"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при создании области: {str(e)}")
    



@router.get("/environment/{environment_id}", response_model=Dict)
async def add_db_to_environment(environment_id: str):
    try:
        environment = db.collection("environments").get(environment_id)
        if not environment:
            raise HTTPException(status_code=404, detail="Окружение не найдено")
        
        databases = db.collection("databases").find({"environment_id": environment_id})
        
        if not databases:
            raise HTTPException(status_code=404, detail="Базы данных не найдены для этого окружения")
        
        databases_data = []
        
        for database in databases:
            tables = db.collection("tables").find({"database_id": database["_key"]})
            tables_data = []

            for table in tables:
                fields = db.collection("fields").find({"table_id": table["_key"]})
                fields_data = []
                
                for field in fields:
                    fields_data.append({
                        "field_name": field["name"],
                        "field_type": field["type"],
                        "constraints": field.get("constraints", ""),
                        "foreign_key": field.get("foreign_key", "")
                    })
                
                tables_data.append({
                    "table_name": table["name"],
                    "fields": fields_data
                })
            
            databases_data.append({
                "database_name": database["name"],
                "tables": tables_data
            })
        
        return {
            "environment_name": environment["name"],
            "databases": databases_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при извлечении данных: {str(e)}")
    