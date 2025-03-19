from fastapi import UploadFile
import re
from handler import inserter



def parse_field_line(line: str):
    line = line.rstrip(',').strip()
    if not line:
        return None

    # line = re.sub(r'\s*DEFAULT\s+[^,]+', '', line)

    tokens = line.split()
    if not tokens:
        return None

    field_name = tokens[0]
    
    constraint_keywords = {"NOT", "NULL", "PRIMARY", "UNIQUE", "CHECK", "REFERENCES", "COLLATE"}

    type_tokens = []
    constraints = []

    i = 1
    while i < len(tokens) and tokens[i].upper() not in constraint_keywords:
        type_tokens.append(tokens[i])
        i += 1

    field_type = " ".join(type_tokens)

    while i < len(tokens):
        constraints.append(tokens[i])
        i += 1

    return field_name, field_type, normalize_constraints(" ".join(constraints))


def normalize_constraints(constraint_str: str) -> str:
    replacements = {
        "NOT NULL": "NOT_NULL",
        "PRIMARY KEY": "PRIMARY_KEY",
        "FOREIGN KEY": "FOREIGN_KEY",
        "CHECK CONSTRAINT": "CHECK_CONSTRAINT",
    }
    for old, new in replacements.items():
        constraint_str = re.sub(rf'\b{old}\b', new, constraint_str, flags=re.IGNORECASE)
    return constraint_str


def parse_sql_dump(env_id: str, sql_dump: str):
    db_name = "default_db"
    db_name_match = re.search(r"CREATE DATABASE (\S+)", sql_dump, re.IGNORECASE)

    if db_name_match:
        db_name = db_name_match.group(1)

    db_id = inserter.upload_database(environment_id=env_id, db_name=db_name)

    table_constraints = parse_table_level_constraints(sql_dump)

    table_pattern = re.compile(
        r"CREATE\s+TABLE\s+(?:\"?(\w+)\"?\.)?\"?(\w+)\"?\s*\((.*?)\);",
        re.IGNORECASE | re.DOTALL
    )

    tables = table_pattern.findall(sql_dump)
    if not tables:
        return
    
    for schema, table_name, table_body in tables:
        full_table_name = f"{schema}.{table_name}" if schema else table_name

        table_id = inserter.upload_table(db_id, full_table_name)
        
        tbl_constraints = table_constraints.get(full_table_name, {})
        pk_columns = tbl_constraints.get("primary_key", set())
        unique_constraints = tbl_constraints.get("unique", [])
        fk_constraints = tbl_constraints.get("foreign_keys", [])

        lines = table_body.splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if re.match(r'^(CONSTRAINT|PRIMARY|FOREIGN|UNIQUE|CHECK)', line, re.IGNORECASE):
                continue
            
            field_info = parse_field_line(line)
            if field_info:
                field_name, field_type, inline_constraints = field_info
                extra_info = set()
                foreign_key = None

                if inline_constraints:
                    extra_info.add(inline_constraints)
                if field_name in pk_columns:
                    extra_info.add("PRIMARY_KEY")
                for uniq in unique_constraints:
                    if field_name in uniq:
                        extra_info.add("UNIQUE")
                for fk in fk_constraints:
                    if field_name in fk["columns"]:
                        foreign_key = f"{fk['ref_table']}({', '.join(fk['ref_columns'])})"

                all_constraints = " ".join(extra_info).strip()
                output = field_name + " " + field_type + " " + all_constraints if all_constraints else field_name + " " + field_type
                
                inserter.upload_field(table_id, field_name, field_type, all_constraints, foreign_key)

            else:
                print(f"  [Не удалось разобрать]: {line}")


def parse_table_level_constraints(sql_dump: str):
    constraints = {}

    # PRIMARY KEY
    alter_pk_pattern = re.compile(
        r"ALTER\s+TABLE\s+(?:ONLY\s+)?(?:\"?(\w+)\"?\.)?\"?(\w+)\"?\s+ADD\s+CONSTRAINT\s+\w+\s+PRIMARY\s+KEY\s*\((.*?)\)\s*;",
        re.IGNORECASE | re.DOTALL
    )
    for schema, table, columns in alter_pk_pattern.findall(sql_dump):
        table_full_name = f"{schema}.{table}" if schema else table
        cols = {col.strip(' "')
                for col in columns.split(',')}
        if table_full_name not in constraints:
            constraints[table_full_name] = {}
        constraints[table_full_name]["primary_key"] = cols

    # UNIQUE
    alter_unique_pattern = re.compile(
        r"ALTER\s+TABLE\s+(?:ONLY\s+)?(?:\"?(\w+)\"?\.)?\"?(\w+)\"?\s+ADD\s+CONSTRAINT\s+\w+\s+UNIQUE\s*\((.*?)\)\s*;",
        re.IGNORECASE | re.DOTALL
    )
    for schema, table, columns in alter_unique_pattern.findall(sql_dump):
        table_full_name = f"{schema}.{table}" if schema else table
        cols = {col.strip(' "')
                for col in columns.split(',')}
        if table_full_name not in constraints:
            constraints[table_full_name] = {}
        constraints[table_full_name].setdefault("unique", []).append(cols)

    # FOREIGN KEY
    alter_fk_pattern = re.compile(
        r"ALTER\s+TABLE\s+(?:ONLY\s+)?(?:\"?(\w+)\"?\.)?\"?(\w+)\"?\s+ADD\s+CONSTRAINT\s+\w+\s+FOREIGN\s+KEY\s*\((.*?)\)\s+REFERENCES\s+(?:\"?(\w+)\"?\.)?\"?(\w+)\"?\s*\((.*?)\)\s*;",
        re.IGNORECASE | re.DOTALL
    )
    for schema, table, columns, ref_schema, ref_table, ref_columns in alter_fk_pattern.findall(sql_dump):
        table_full_name = f"{schema}.{table}" if schema else table
        cols = {col.strip(' "')
                for col in columns.split(',')}
        ref_table_full = f"{ref_schema}.{ref_table}" if ref_schema else ref_table
        ref_cols = {col.strip(' "')
                    for col in ref_columns.split(',')}
        if table_full_name not in constraints:
            constraints[table_full_name] = {}
        constraints[table_full_name].setdefault("foreign_keys", []).append({
            "columns": cols,
            "ref_table": ref_table_full,
            "ref_columns": ref_cols
        })

    return constraints


def parse_sql_file(file: UploadFile, env_id: str):
    try:
        file.file.seek(0)
        
        sql_dump = file.file.read().decode("utf-8")

        if not sql_dump.strip():
            ("Файл пустой или не содержит SQL-кода")
            return

        parse_sql_dump(env_id, sql_dump)
    
    except Exception as e:
        print(f"Произошла ошибка при чтении SQL-файла: {e}")
