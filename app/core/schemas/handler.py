from pydantic import BaseModel


class UserBase(BaseModel):
    username: str

class UserRead(UserBase):
    id: int



class EnvironmentCreateRequest(BaseModel):
    name: str


class DatabaseCreateRequest(BaseModel):
    environment_id: str
    name: str


class UpdateForeignKeyRequest(BaseModel):
    foreign_key: str
