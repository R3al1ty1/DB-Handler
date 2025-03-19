import traceback
from typing import List, Dict

from core.crud.fields import db_delete_fields, db_get_fields
from core.settings import settings


db = settings.db.db_client


async def db_get_tables(db_id: str) -> List:
    """"""
    try:
        tables = db.collection("tables").find({"database_id": db_id})
            
        tables_data = []
        for table in tables:
            fields_data = await db_get_fields(table_id=table["_key"])

            tables_data.append({
                    "table_id": table["_key"],
                    "table_name": table["name"],
                    "fields": fields_data
                })

        return tables_data

    except:
        traceback.print_exc()
        return False


async def db_get_table_specific(table_id: str) -> Dict:
    try:
        table = db.collection("tables").get(table_id)
            
        fields_data = await db_get_fields(table_id=table["_key"])

        return {
            "table_id": table_id,
            "table_name": table["name"],
            "fields": fields_data
        }

    except Exception as e:
        traceback.print_exc()
        return False


async def db_change_table_name(
        table_id: str,
        new_name: str
    ) -> Dict:
    """"""
    try:
        table = db.collection("tables").find({"_key": table_id})
        
        table["name"] = new_name
        db.collection("tables").update(table)

        new_table = await db_get_table_specific(table_id=table_id)

        return new_table

    except:
        traceback.print_exc()
        return False


async def db_delete_tables(db_id: str) -> bool:
    """"""
    try:
        tables = db.collection("tables").find({"database_id": db_id})
        for table in tables:
            await db_delete_fields(table["_key"])
            db.collection("tables").delete(table["_key"])
        
        return True

    except:
        traceback.print_exc()
        return False
