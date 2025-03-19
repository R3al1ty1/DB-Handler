import traceback
from typing import Optional, Dict

from core.settings import settings


db = settings.db.db_client


async def db_get_fields(table_id: str) -> Dict:
    """"""
    try:
        fields = db.collection("fields").find({"table_id": table_id})

        fields_data = []

        for field in fields:
            fields_data.append({
                "field_id": field["_key"],
                "field_name": field["name"],
                "field_type": field["type"],
                "constraints": field.get("constraints", ""),
                "foreign_key": field.get("foreign_key", "")
            })

        return fields_data

    except:
        traceback.print_exc()
        return False
    

async def db_get_field_specific(field_id: str) -> Dict:
    """"""
    try:
        field = db.collection("fields").find({"_key": field_id})
        
        return {
                "field_id": field["_key"],
                "field_name": field["name"],
                "field_type": field["type"],
                "constraints": field.get("constraints", ""),
                "foreign_key": field.get("foreign_key", "")
            }

    except:
        traceback.print_exc()
        return False
    

async def db_delete_fields(table_id: str) -> bool:
    """"""
    try:
        fields = db.collection("fields").find({"_key": table_id})
        for field in fields:
            db.collection("fields").delete(field["_key"])
        
        return True

    except:
        traceback.print_exc()
        return False
    

async def db_delete_specific_field(field_id: str) -> bool:
    """"""
    try:
        db.collection("fields").delete(field_id)

        return True

    except:
        traceback.print_exc()
        return False


async def db_change_field(
        field_id: str,
        to_change: str,
        change_value: str
    ) -> Dict:
    """"""
    try:
        db.collection("fields").find({"_key": field_id})

        db[to_change] = change_value

        return await db_get_field_specific(field_id=field_id)

    except:
        traceback.print_exc()
        return False


async def db_update_fk(
        field_id: str,
        fk_value: Optional[str]
    ) -> Dict:
    """"""
    try:
        field = db.collection("fields").find({"_key": field_id})
        
        field["foreign_key"] = fk_value

        return await db_get_field_specific(field_id=field_id)

    except:
        traceback.print_exc()
        return False
