import asyncio
import traceback
import json
import os
from typing import Dict, List
from dotenv import load_dotenv

from app.core.settings import settings


load_dotenv()

DB_USERNAME = os.getenv("APP_CONFIG__DB__USERNAME")
DB_PASSWORD = os.getenv("APP_CONFIG__DB__PASSWORD")


async def get_db(name: str = "new_env"):
    """Функция создания/получения единой БД для экспорта."""
    try:
        client = settings.db.client
        sys_db = client.db('_system', username=DB_USERNAME, password=DB_PASSWORD)
        if not sys_db.has_database(name=name):
            sys_db.create_database(name=name)
            print(f"Создана новая база данных: {name}")
            db = client.db(name, username=DB_USERNAME, password=DB_PASSWORD)
        else:
            print(f"Подключение к существующей базе данных: {name}")
            db = client.db(name, username=DB_USERNAME, password=DB_PASSWORD)
        
        return db
    except Exception as e:
        traceback.print_exc()
        print(f"Ошибка при создании/получении базы данных: {e}")
        return None


async def create_collections(db, tables: List[Dict], source_db_name: str):
    """Функция создания коллекций на основе списка таблиц."""
    try:
        collections_created = []
        
        for table in tables:
            original_table_name = table["table_name"]
            table_name = original_table_name.split(".")[-1] if "." in original_table_name else original_table_name
            
            if not db.has_collection(table_name):
                collection = db.create_collection(name=table_name)
                collections_created.append(table_name)
                print(f"Создана коллекция: {table_name} (из {original_table_name})")
            else:
                print(f"Коллекция {table_name} уже существует")
                
        return collections_created
    except Exception as e:
        traceback.print_exc()
        print(f"Ошибка при создании коллекций: {e}")
        return []


async def create_schema_collection(db):
    """Создаем коллекцию для хранения схем/структур таблиц"""
    try:
        schema_collection_name = "schema_definitions"
        if not db.has_collection(schema_collection_name):
            db.create_collection(name=schema_collection_name)
            print(f"Создана коллекция для метаданных: {schema_collection_name}")
        else:
            print(f"Коллекция {schema_collection_name} для метаданных уже существует")
        
        return True
    except Exception as e:
        traceback.print_exc()
        print(f"Ошибка при создании коллекции метаданных: {e}")
        return False


async def store_schema_definitions(db, tables: List[Dict], source_db_name: str):
    """Сохраняем структуру/схему каждой таблицы в коллекцию schema_definitions"""
    try:
        schema_collection = db.collection("schema_definitions")
        
        schemas_stored = []
        
        for table in tables:
            original_table_name = table["table_name"]
            table_name = original_table_name.split(".")[-1] if "." in original_table_name else original_table_name
            
            # Формируем документ с метаданными схемы
            schema_doc = {
                "_key": f"{source_db_name}_{table_name}",
                "source_database": source_db_name,
                "original_table_name": original_table_name,
                "collection_name": table_name,
                "fields": table["fields"],
                "created_at": "CURRENT_TIMESTAMP"
            }

            try:
                existing = schema_collection.get(schema_doc["_key"])
                if existing:
                    schema_collection.update(schema_doc)
                    print(f"Обновлена схема для: {table_name}")
                else:
                    schema_collection.insert(schema_doc)
                    print(f"Добавлена схема для: {table_name}")
                
                schemas_stored.append(table_name)

            except Exception as doc_err:
                schema_collection.insert(schema_doc)
                print(f"Добавлена схема для: {table_name}")
                schemas_stored.append(table_name)
        
        return schemas_stored
    except Exception as e:
        traceback.print_exc()
        print(f"Ошибка при сохранении метаданных схем: {e}")
        return []


async def import_all_tables_to_single_db(json_data: Dict, db_name: str = "new_env"):
    """Импорт всех таблиц из всех баз данных в одну базу ArangoDB."""
    try:
        db = await get_db(db_name)
        if not db:
            print(f"Не удалось подключиться к базе данных {db_name}")
            return {}
        
        schema_created = await create_schema_collection(db)
        if not schema_created:
            print("Не удалось создать коллекцию схем")
        
        databases = json_data.get("databases", [])
        
        results = {
            "collections_created": [],
            "schemas_stored": []
        }
        
        for database in databases:
            source_db_name = database.get("database_name")
            tables = database.get("tables", [])
            
            print(f"\nИмпорт таблиц из базы данных '{source_db_name}':")
            
            collections_created = await create_collections(db, tables, source_db_name)
            results["collections_created"].extend(collections_created)
            
            # Сохраняем схемы таблиц
            if schema_created:
                schemas_stored = await store_schema_definitions(db, tables, source_db_name)
                results["schemas_stored"].extend(schemas_stored)
        
        return results
    except Exception as e:
        traceback.print_exc()
        print(f"Ошибка при импорте таблиц: {e}")
        return {"collections_created": [], "schemas_stored": []}


async def load_json_file(file_path: str):
    """Загрузка JSON-файла."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"Ошибка при загрузке JSON-файла: {e}")
        return None


async def main():
    json_file_path = "/Users/user/DB-Handler/app/handler/temp.json"
    
    target_db_name = "new_env"
    
    json_data = await load_json_file(json_file_path)
    if not json_data:
        print("Не удалось загрузить данные из JSON-файла")
        return
    
    # Импортируем все таблицы в единую базу данных и сохраняем их схемы
    results = await import_all_tables_to_single_db(json_data, target_db_name)
    
    print("\nСводка импорта:")
    print(f"База данных: {target_db_name}")
    
    print("\nСозданные коллекции:")
    if results["collections_created"]:
        for collection in results["collections_created"]:
            print(f"  - {collection}")
        print(f"Всего создано коллекций: {len(results['collections_created'])}")
    else:
        print("  Коллекции не созданы или уже существуют")
    
    print("\nСохраненные схемы:")
    if results["schemas_stored"]:
        for schema in results["schemas_stored"]:
            print(f"  - {schema}")
        print(f"Всего сохранено схем: {len(results['schemas_stored'])}")
    else:
        print("  Схемы не сохранены")


# if __name__ == "__main__":
#     asyncio.run(main())