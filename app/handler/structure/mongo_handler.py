import json
import re
from fastapi import UploadFile
import inserter

def preprocess_mongo_dump(dump_str: str) -> str:
    """
    Преобразует MongoDB-специфичные конструкции в валидный JSON:
      - ObjectId("...") -> "..."
      - NumberInt(123)   -> 123
    """
    dump_str = re.sub(r'ObjectId\("([^"]+)"\)', r'"\1"', dump_str)
    dump_str = re.sub(r'NumberInt\((\d+)\)', r'\1', dump_str)
    return dump_str

def infer_field_type(value) -> str:
    """
    Определяет тип поля на основе значения.
    Возвращаемые типы: string, number, boolean, object, array, date или mixed (если типы не совпадают).
    """
    if isinstance(value, bool):
        return "boolean"
    elif isinstance(value, int) or isinstance(value, float):
        return "number"
    elif isinstance(value, list):
        return "array"
    elif isinstance(value, dict):
        return "object"
    elif isinstance(value, str):
        # Простейшая проверка на дату по формату ISO
        iso_date_regex = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'
        if re.match(iso_date_regex, value):
            return "date"
        return "string"
    return "string"

def parse_mongo_dump(env_id: str, mongo_dump: str):
    """
    Анализирует дамп MongoDB в формате JSON, определяет коллекции (на основании верхнеуровневых ключей)
    и вычисляет схему для каждой коллекции (объединение всех полей документов).
    Для каждого поля применяется простая эвристика: 
      - если имя поля равно "_id" – оно считается PRIMARY_KEY;
      - если имя поля заканчивается на "_id" и имя без суффикса совпадает с именем другой коллекции – FOREIGN_KEY.
    Затем данные загружаются в ArangoDB через inserter.
    """
    # Приводим дамп к валидному JSON и парсим его
    mongo_dump = preprocess_mongo_dump(mongo_dump)
    data = json.loads(mongo_dump)
    
    # Определяем имя базы (можно доработать логику определения)
    db_name = "mongodb_db"
    db_id = inserter.upload_database(env_id, db_name)
    
    # Считаем, что все верхнеуровневые ключи (кроме служебного "_id") — это коллекции
    collections = {key: value for key, value in data.items() if key != "_id"}
    collection_names = set(collections.keys())
    
    for coll_name, documents in collections.items():
        # Загружаем коллекцию как таблицу в ArangoDB
        table_id = inserter.upload_table(db_id, coll_name)
        
        if not documents:
            continue
        
        # Определяем схему коллекции: объединяем все поля из документов
        schema = {}
        for doc in documents:
            for field, value in doc.items():
                current_type = infer_field_type(value)
                if field in schema:
                    # При несовпадении типов выбираем универсальный тип "mixed"
                    if schema[field] != current_type:
                        schema[field] = "mixed"
                else:
                    schema[field] = current_type
        
        # Обрабатываем каждое поле коллекции
        for field_name, field_type in schema.items():
            constraints = []
            foreign_key = None
            
            if field_name == "_id":
                constraints.append("PRIMARY_KEY")
            elif field_name.endswith("_id"):
                # Простейшая эвристика для определения внешнего ключа:
                # если имя поля без "_id" совпадает с именем другой коллекции (в единственном или во множественном числе)
                candidate = field_name[:-3]
                if candidate in collection_names or candidate + "s" in collection_names:
                    constraints.append("FOREIGN_KEY")
                    foreign_key = candidate if candidate in collection_names else candidate + "s"
            
            inserter.upload_field(table_id, field_name, field_type, " ".join(constraints), foreign_key)

def parse_mongo_file(file: UploadFile, env_id: str):
    """
    Читает загруженный файл (UploadFile) с дампом MongoDB, декодирует его и запускает парсинг.
    """
    try:
        file.file.seek(0)
        mongo_dump = file.file.read().decode("utf-8")
        
        if not mongo_dump.strip():
            print("Файл пустой или не содержит данных")
            return
        
        parse_mongo_dump(env_id, mongo_dump)
    
    except Exception as e:
        print(f"Ошибка при чтении MongoDB файла: {e}")
