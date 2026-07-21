from pydantic import BaseModel

from src.core.config import Environment


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: Environment
    version: str

