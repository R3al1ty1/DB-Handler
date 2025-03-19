from fastapi import APIRouter, HTTPException, File, UploadFile, Form, Request
from typing import List, Dict

from handler.structure.postgres_handler import parse_sql_file
from core.settings import settings
from core.crud.databases import db_delete_database, db_get_database_specific, db_get_databases


db = settings.db.db_client

router = APIRouter(
    # prefix=settings.api.v1.prefix,
    tags=["Databases"]
)

# @router.get("/databases/{env_id}", response_model=List[Dict])
# async def get_databases(
#         env_id: str
#     ):
#     try:
#         databases = await db_get_databases(env_id=env_id)
#         if not databases:
#             raise HTTPException(status_code=404, detail="Базы данных не найдены")

#         return databases

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Ошибка при извлечении данных: {str(e)}")


@router.get("/databases/{db_id}", response_model=Dict)
async def get_specific_database(db_id: str):
    try:
        database = await db_get_database_specific(db_id=db_id)
        if not database:
            raise HTTPException(status_code=404, detail="База данных не найдена")
        
        return database
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при извлечении данных: {str(e)}")
    

@router.post("/database/add", response_model=Dict)
async def add_database(
    environment_id: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        environment = db.collection("environments").get(environment_id)
        if not environment:
            raise HTTPException(status_code=404, detail="Окружение не найдено")

        sql_content = await file.read()
        sql_content.decode("utf-8")
        
        parse_sql_file(file, environment_id )

        return {
            "message": f"База данных '{file.filename}' успешно создана и привязана к окружению '{environment_id}'",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при создании базы данных: {str(e)}")


@router.delete("/database/delete/{db_id}", response_model=dict)
async def delete_database(db_id: str):
    try:
        res = await db_delete_database(db_id=db_id)
        if not res:
            raise HTTPException(status_code=404, detail="База данных не найдена")

        return {"message": f"База данных с ID '{db_id}' успешно удалена"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении базы данных: {str(e)}")
