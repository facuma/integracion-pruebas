from sqlalchemy import Column, Integer, String, DateTime, func, Text
from app.db import Base


class User(Base): 
    """
    Local user storage for api-compras.
    Frontend handles authentication, we just store basic info.
    user_id is whatever identifier the frontend sends us (could be email, UUID, etc)
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    
    # External user ID (from frontend's auth system)
    user_id = Column(String(255), unique=True, index=True, nullable=False)
    
    # Optional user info
    nombre = Column(String(150), nullable=True)
    email = Column(String(150), unique=True, index=True, nullable=True)
    
    # Optional extra data from frontend (JSON string)
    extra_data = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)