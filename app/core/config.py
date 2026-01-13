from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List
import os


class Settings(BaseSettings):
    # MongoDB - support both naming conventions
    MONGODB_URL: str = Field(
        default="mongodb+srv://dbUser:dbUserPassword@procruitlycluster.z3egqzn.mongodb.net/?retryWrites=true&w=majority&appName=ProcruitlyCluster",
        validation_alias="MONGO_URI"
    )
    DATABASE_NAME: str = Field(default="ajrak", validation_alias="DB_NAME")
    
    # MinIO
    MINIO_ENDPOINT: str = "212.85.26.87:9000"
    MINIO_ACCESS_KEY: str = "ajrak"
    MINIO_SECRET_KEY: str = "Admin@ajrak1805"
    MINIO_BUCKET: str = "ajrak"
    MINIO_SECURE: bool = False
    
    # JWT
    SECRET_KEY: str = "ajrak-secret-key-2025-luxury-fashion"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:5174"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()

