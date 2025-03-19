from fastapi import APIRouter, HTTPException

from core.crud.tables import db_change_table_name, db_get_table_specific
from core.settings import settings


db = settings.db.db_client

router = APIRouter(
    # prefix=settings.api.v1.prefix,
    tags=["Tables"]
)


@router.get("/tables/{table_id}", response_model=dict)
async def get_table(table_id: str):
    try:
        table = await db_get_table_specific(table_id=table_id)

        if not table:
            raise HTTPException(status_code=404, detail="Таблица не найдена")

        return table
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при извлечении таблицы: {str(e)}")
    

@router.patch("/tables/name/{table_id}", response_model=dict)
async def change_table_name(table_id: str):
    try:
        table = await db_change_table_name(table_id=table_id)

        if not table:
            raise HTTPException(status_code=404, detail="Таблица не найдена")

        return table

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении таблицы: {str(e)}")


@router.delete("/tables/delete/{table_id}", response_model=dict)
async def delete_table(table_id: str):
    try:
        table = db.collection("tables").get(table_id)
        if not table:
            raise HTTPException(status_code=404, detail="Таблица не найдена")

        fields = db.collection("fields").find({"table_id": table_id})
        for field in fields:
            db.collection("fields").delete(field["_key"])

        db.collection("tables").delete(table_id)

        return {"message": f"Таблица с ID '{table_id}' успешно удалена"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении таблицы: {str(e)}")
