import traceback
from typing import Dict, List
from core.settings import settings
from core.crud.tables import db_delete_tables, db_get_tables


db = settings.db.db_client


async def db_get_databases(
        env_id: str
    ) -> List:
    """"""
    try:
        databases = db.collection("databases").find({"environment_id": env_id})
        databases_data = []

        for database in databases:
            tables_data = await db_get_tables(db_id=database["_key"])

            databases_data.append({
                "database_id": database["_key"],
                "database_name": database["name"],
                "tables": tables_data
            })

        return databases_data

    except:
        traceback.print_exc()
        return False


async def db_get_database_specific(
        db_id: str
    ) -> Dict:
    """"""
    try:
        database = db.collection("databases").get(db_id)
        
        tables_data = await db_get_tables(db_id=db_id)

        return {
            "databse_id": db_id,
            "database_name": database["name"],
            "tables": tables_data
        }

    except:
        traceback.print_exc()
        return False


async def db_delete_database(db_id: str) -> bool:
    """"""
    try:
        await db_delete_tables(db_id=db_id)
        db.collection("databases").delete(db_id)

        return True

    except:
        traceback.print_exc()
        return False
