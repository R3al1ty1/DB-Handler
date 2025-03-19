from pydantic import BaseModel


class DatabaseCreateRequest(BaseModel):
    environment_id: str
    name: str
