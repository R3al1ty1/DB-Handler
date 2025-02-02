from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from typing import List, Dict
from handler.postgres_handler import parse_sql_file

from core.settings import settings


db = settings.db.db_client

router = APIRouter(
    prefix=settings.api.v1.arango,
    tags=["Databases"]
)

@router.get("/databases", response_model=List[Dict])
async def get_databases():
    try:
        databases = db.collection("databases").all()
        return [database for database in databases]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при извлечении данных: {str(e)}")


@router.get("/databases/{db_id}", response_model=Dict)
async def get_database(db_id: str):
    try:
        database = db.collection("databases").get(db_id)
        if not database:
            raise HTTPException(status_code=404, detail="База данных не найдена")
        
        tables = db.collection("tables").find({"database_id": db_id})
        
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
        
        return {
            "database_name": database["name"],
            "tables": tables_data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при извлечении данных: {str(e)}")
    

@router.post("/database/add", response_model=Dict)
async def create_database(
    environment_id: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        environment = db.collection("environments").get(environment_id)
        if not environment:
            raise HTTPException(status_code=404, detail="Окружение не найдено")

        sql_content = await file.read()
        sql_text = sql_content.decode("utf-8")
        
        parse_sql_file(file, environment_id )

        return {
            "message": f"База данных '{file.filename}' успешно создана и привязана к окружению '{environment_id}'",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при создании базы данных: {str(e)}")

@router.delete("/database/{db_id}", response_model=dict)
async def delete_database(db_id: str):
    try:
        database = db.collection("databases").get(db_id)
        if not database:
            raise HTTPException(status_code=404, detail="База данных не найдена")

        db.collection("databases").delete(db_id)

        tables = db.collection("tables").find({"database_id": db_id})
        for table in tables:
            db.collection("tables").delete(table["_key"])

            fields = db.collection("fields").find({"table_id": table["_key"]})
            for field in fields:
                db.collection("fields").delete(field["_key"])

        return {"message": f"База данных с ID '{db_id}' успешно удалена"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении базы данных: {str(e)}")
