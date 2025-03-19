from pydantic import BaseModel


class EnvironmentCreateRequest(BaseModel):
    name: str
