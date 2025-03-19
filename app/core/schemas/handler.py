from pydantic import BaseModel


class UserBase(BaseModel):
    username: str

class UserRead(UserBase):
    id: int
