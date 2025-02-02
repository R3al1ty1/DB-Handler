from fastapi import APIRouter, HTTPException
from core.settings import settings


db = settings.db.db_client

router = APIRouter(
    prefix=settings.api.v1.arango,
    tags=["Fields"]
)


@router.patch("/field/{field_from}/{field_to}/foreign_key", response_model=dict)
async def update_foreign_key(field_from: str, field_to: str):
    try:
        field = db.collection("fields").get(field_from)
        if not field:
            raise HTTPException(status_code=404, detail="Поле с таким ID не найдено")

        field["foreign_key"] = field_to

        db.collection("fields").update(field)
        
        return {"message": f"Поле с ID '{field_from}' успешно обновлено, новый внешний ключ: '{field_to}'"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении внешнего ключа: {str(e)}")


@router.patch("/field/{field_id}/remove_foreign_key", response_model=dict)
async def remove_foreign_key(field_id: str):
    try:
        field = db.collection("fields").get(field_id)
        if not field:
            raise HTTPException(status_code=404, detail="Поле с таким ID не найдено")
        field["foreign_key"] = None

        db.collection("fields").update(field)
        
        return {"message": f"Внешний ключ поля с ID '{field_id}' успешно удален"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении внешнего ключа: {str(e)}")
