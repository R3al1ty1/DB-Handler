import traceback
from fastapi import APIRouter, HTTPException
from core.settings import settings


db = settings.db.db_client

router = APIRouter(
    # prefix=settings.api.v1.prefix,
    tags=["Fields"]
)


@router.patch("/fields/{field_from}/{field_to}/foreign_key", response_model=dict)
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


@router.patch("/fields/{field_id}/remove_foreign_key", response_model=dict)
async def remove_foreign_key(field_id: str):
    try:
        field = db.collection("fields").get(field_id)
        db_id = field["database_id"]
        if not field:
            raise HTTPException(status_code=404, detail="Поле с таким ID не найдено")
        field["foreign_key"] = None

        db.collection("fields").update(field)
        
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
                    "field_id": field["_key"],
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
            "databse_id": database["_key"],
            "database_name": database["name"],
            "tables": tables_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении внешнего ключа: {str(e)}")
    

@router.patch("/fields/change/{field_id}")
async def change_field(field_id: str):
    try:
        pass

    except:
        traceback.print_exc()