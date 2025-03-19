from pydantic import BaseModel


class UpdateForeignKeyRequest(BaseModel):
    foreign_key: str
