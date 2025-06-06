from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import logging
from typing import Optional
import os
from .init_db import init_database

logger = logging.getLogger(__name__)

class DatabaseManager:
    _instance: Optional['DatabaseManager'] = None
    _client: Optional[AsyncIOMotorClient] = None
    _db: Optional[AsyncIOMotorDatabase] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance

    @classmethod
    async def initialize(cls, mongodb_url: Optional[str] = None, db_name: Optional[str] = None) -> AsyncIOMotorDatabase:
        """
        Initialize the database connection and schema.
        This should be called once at application startup.
        """
        if cls._db is not None:
            return cls._db

        # Use environment variables with fallbacks
        mongodb_url = mongodb_url or os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        db_name = db_name or os.getenv("MONGODB_DB_NAME", "adhd_coach")

        try:
            # Create client
            cls._client = AsyncIOMotorClient(mongodb_url)
            
            # Initialize database with schema
            cls._db = await init_database(cls._client, db_name)
            
            logger.info(f"Database connection established to {db_name}")
            return cls._db
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            if cls._client:
                cls._client.close()
            raise

    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        """
        Get the database instance.
        Raises RuntimeError if database hasn't been initialized.
        """
        if cls._db is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return cls._db

    @classmethod
    async def close(cls):
        """Close the database connection."""
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None
            logger.info("Database connection closed")

# Usage example:
# async def startup():
#     await DatabaseManager.initialize()
# 
# async def shutdown():
#     await DatabaseManager.close()
# 
# # In your FastAPI app:
# from fastapi import FastAPI
# app = FastAPI()
# 
# @app.on_event("startup")
# async def startup_db():
#     await DatabaseManager.initialize()
# 
# @app.on_event("shutdown")
# async def shutdown_db():
#     await DatabaseManager.close() 