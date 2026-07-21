from pydantic import BaseModel, Field

from src.core.config import Environment


class HealthResponse(BaseModel):
    status: str = Field(description="Overall service status: 'ok' or 'degraded'.")
    service: str = Field(description="Service name.")
    environment: Environment = Field(description="Active runtime environment.")
    version: str = Field(description="Current API version.")
    database: str = Field(default="ok", description="Database connection health status.")
