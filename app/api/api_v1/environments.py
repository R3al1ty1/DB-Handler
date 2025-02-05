from fastapi import APIRouter, HTTPException
from typing import Dict, List

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



@router.get("/environments", response_model=Dict[str, List[Dict]])
async def get_environments():
    try:
        environments = db.collection("environments").all()
        if not environments:
            raise HTTPException(status_code=404, detail="Окружения не найдены")

        result = []

        for environment in environments:
            try:
                databases = db.collection("databases").find({"environment_id": environment["_key"]})
            except Exception:
                databases = []

            databases_data = []

            for database in databases:
                tables = db.collection("tables").find({"database_id": database["_key"]})
                tables_data = []

                for table in tables:
                    fields = db.collection("fields").find({"table_id": table["_key"]})
                    fields_data = [
                        {
                            "field_name": field["name"],
                            "field_type": field["type"],
                            "constraints": field.get("constraints", ""),
                            "foreign_key": field.get("foreign_key", "")
                        }
                        for field in fields
                    ]

                    tables_data.append({
                        "table_name": table["name"],
                        "fields": fields_data
                    })

                databases_data.append({
                    "database_name": database["name"],
                    "tables": tables_data
                })

            result.append({
                "environment_name": environment["name"],
                "databases": databases_data
            })

        return {"environments": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при извлечении данных: {str(e)}")


@router.get("/environments/{environment_id}", response_model=Dict)
async def get_databases_for_environment(environment_id: str):
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
    