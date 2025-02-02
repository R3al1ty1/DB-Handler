from pydantic_settings import BaseSettings, SettingsConfigDict
from arango import ArangoClient
from pydantic import BaseModel
from typing import ClassVar
import os
from dotenv import load_dotenv


load_dotenv()

class RunConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000


class ApiV1Prefix(BaseModel):
    prefix: str = "/v1"
    arango: str = "/arango"


class ApiPrefix(BaseModel):
    prefix: str = "/api"
    v1: ApiV1Prefix = ApiV1Prefix()


class ArangoDBConfig(BaseModel):
    host: str = os.getenv("APP_CONFIG__DB__HOST")
    port: int = int(os.getenv("APP_CONFIG__DB__PORT"))
    username: str = os.getenv("APP_CONFIG__DB__USERNAME")
    password: str = os.getenv("APP_CONFIG__DB__PASSWORD")
    db_name: str = os.getenv("APP_CONFIG__DB__DB_NAME")

    client: ClassVar[ArangoClient] = ArangoClient(hosts=host)
    db_client: ClassVar = client.db(db_name, username=username, password=password)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
    )
    run: RunConfig = RunConfig()
    api: ApiPrefix = ApiPrefix()
    db: ArangoDBConfig = ArangoDBConfig()

settings = Settings()