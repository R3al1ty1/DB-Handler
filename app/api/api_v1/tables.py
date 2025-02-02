from fastapi import APIRouter, HTTPException
from core.settings import settings


db = settings.db.db_client

router = APIRouter(
    prefix=settings.api.v1.arango,
    tags=["Tables"]
)


@router.delete("/table/{table_id}", response_model=dict)
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
