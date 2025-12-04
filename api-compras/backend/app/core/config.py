from pydantic import BaseModel
import os

class Settings(BaseModel):
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-prod")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # ajusta a tu gusto
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

settings = Settings()
