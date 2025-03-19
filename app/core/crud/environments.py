import traceback
from typing import List, Dict

from handler.inserter import generate_id
from core.crud.databases import db_delete_database, db_get_databases
from core.settings import settings


db = settings.db.db_client


async def db_create_environment(env_name: str) -> str:
    """"""
    try:
        existing_environment = db.collection("environments").find({"name": env_name})
        if existing_environment:
            return False

        environment_id = generate_id()
        db.collection("environments").insert({"_key": environment_id, "name": env_name})

        return environment_id

    except:
        traceback.print_exc()
        return False


async def db_get_environments() -> List:
    """"""
    try:
        environments = db.collection("environments").all()

        environments_data = []

        for environment in environments:
            env_id = environment["_key"]
            databases_data = await db_get_databases(env_id=env_id)

            environments_data.append({
                    "environment_id": env_id,
                    "environment_name": environment["name"],
                    "databases": databases_data
                })
        
        return environments_data

    except:
        traceback.print_exc()
        return False


async def db_get_environment_specific(env_id: str) -> Dict:
    """"""
    try:
        environment = db.collection("environments").get(env_id)
        
        databases_data = await db_get_databases(env_id=env_id)

        return {
            "environment_id": env_id,
            "environment_name": environment["name"],
            "databases": databases_data
        }

    except:
        traceback.print_exc()
        return False


async def db_delete_environment(env_id: str) -> bool:
    """"""
    try:
        databases = db.collection("databases").find({"environment_id": env_id})
        
        for database in databases:
            await db_delete_database(db_id=database["_key"])

        db.collection("environments").delete(env_id)

        return True

    except:
        traceback.print_exc()
        return False
