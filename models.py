from sqlalchemy import Column, Integer, String, DateTime, create_engine, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum
import os
import hashlib
from config import DATABASE_URL

Base = declarative_base()

class TaskStatus(enum.Enum):
    PENDING = "pending"
    CONVERTING = "converting"
    SUCCEED = "succeed"
    FAILED = "failed"

class ImageTask(Base):
    __tablename__ = 'image_tasks'
    
    id = Column(Integer, primary_key=True)
    original_url = Column(String, unique=True, index=True, nullable=False)
    original_url_hash = Column(String, unique=True, index=True, nullable=False)
    original_filename = Column(String, nullable=True)
    format = Column(String, nullable=False)  # 'webp' or 'avif'
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    result_path = Column(String, nullable=True)
    query_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    @staticmethod
    def url_to_hash(url, format=None):
        if format:
            hash_content = f"{url}:{format}"
        else:
            hash_content = url
        return hashlib.sha256(hash_content.encode()).hexdigest()
    

def init_db():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine) 