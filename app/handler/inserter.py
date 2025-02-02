from core.settings import settings
import uuid
from arango import ArangoClient


db = settings.db.db_client

def generate_collections():
    client = ArangoClient(hosts=settings.db.host)
    sys_db = client.db("_system", username=settings.db.username, password=settings.db.password)

    if not sys_db.has_database(settings.db.db_name):
        sys_db.create_database(settings.db.db_name)

    db = client.db(settings.db.db_name, username=settings.db.username, password=settings.db.password)

    collections = ["environments", "databases", "tables", "fields"]
    for collection in collections:
        if not db.has_collection(collection):
            db.create_collection(collection)
            print(f"✅ Коллекция '{collection}' создана.")
        else:
            print(f"⚡ Коллекция '{collection}' уже существует.")

def generate_id():
    """Генерирует уникальный идентификатор."""
    return str(uuid.uuid4())


def upload_environment(environment_name):
    """Загружает область в ArangoDB и возвращает её ID."""
    environment_id = generate_id()
    db.collection("environments").insert({"_key": environment_id, "name": environment_name})
    return environment_id


def upload_database(environment_id: str, db_name: str):
    """Загружает информацию о базе данных в коллекцию и связывает с окружением."""
    db_id = generate_id()
    db.collection("databases").insert({
        "_key": db_id,
        "name": db_name,
        "environment_id": environment_id
    })
    return db_id


def upload_table(db_id, table_name):
    """Загружает таблицу в ArangoDB и связывает её с конкретной базой данных."""
    table_id = generate_id()
    db.collection("tables").insert({"_key": table_id, "database_id": db_id, "name": table_name})
    return table_id


def upload_field(table_id, field_name, field_type, constraints, foreign_key=None):
    """Загружает поле в ArangoDB, включая информацию о внешнем ключе."""
    field_data = {
        "_key": generate_id(),
        "table_id": table_id,
        "name": field_name,
        "type": field_type,
        "constraints": constraints if constraints else None,
    }
    
    if foreign_key:
        field_data["foreign_key"] = foreign_key

    db.collection("fields").insert(field_data)
