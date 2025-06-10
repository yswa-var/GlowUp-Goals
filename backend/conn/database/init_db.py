from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Dict, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Schema definitions
COLLECTIONS = {
    "users": {
        "validator": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["email", "password_hash", "created_at", "preferences"],
                "properties": {
                    "email": {"bsonType": "string"},
                    "password_hash": {"bsonType": "string"},
                    "created_at": {"bsonType": "date"},
                    "preferences": {
                        "bsonType": "object",
                        "required": ["check_in_interval", "theme"],
                        "properties": {
                            "check_in_interval": {"bsonType": "int"},
                            "theme": {"bsonType": "string"}
                        }
                    }
                }
            }
        },
        "indexes": [
            {"keys": [("email", 1)], "unique": True},
            {"keys": [("created_at", 1)]}
        ]
    },
    "tasks": {
        "validator": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["user_id", "title", "status", "created_at", "task_order"],
                "properties": {
                    "user_id": {"bsonType": "objectId"},
                    "title": {"bsonType": "string"},
                    "description": {"bsonType": "string"},
                    "estimated_time": {"bsonType": "string"},
                    "repeat": {
                        "bsonType": "object",
                        "required": ["enabled"],
                        "properties": {
                            "enabled": {"bsonType": "string", "enum": ["yes", "no"]},
                            "interval": {"bsonType": "string"}
                        }
                    },
                    "due_date": {"bsonType": "date"},
                    "status": {"bsonType": "string"},
                    "created_at": {"bsonType": "date"},
                    "completed_at": {"bsonType": "date"},
                    "task_order": {"bsonType": "int"}
                }
            }
        },
        "indexes": [
            {"keys": [("user_id", 1), ("created_at", -1)]},
            {"keys": [("status", 1)]},
            {"keys": [("due_date", 1)]},
            {"keys": [("user_id", 1), ("task_order", 1)], "unique": True}
        ]
    },
    "moods": {
        "validator": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["user_id", "score", "timestamp"],
                "properties": {
                    "user_id": {"bsonType": "objectId"},
                    "score": {"bsonType": "int"},
                    "description": {"bsonType": "string"},
                    "task_id": {"bsonType": "objectId"},
                    "timestamp": {"bsonType": "date"}
                }
            }
        },
        "indexes": [
            {"keys": [("user_id", 1), ("timestamp", -1)]},
            {"keys": [("task_id", 1)]}
        ]
    },
    "logs": {
        "validator": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["user_id", "message", "is_user", "timestamp"],
                "properties": {
                    "user_id": {"bsonType": "objectId"},
                    "message": {"bsonType": "string"},
                    "is_user": {"bsonType": "bool"},
                    "timestamp": {"bsonType": "date"}
                }
            }
        },
        "indexes": [
            {"keys": [("user_id", 1), ("timestamp", -1)]},
            {"keys": [("is_user", 1)]}
        ]
    }
}

class DatabaseInitializer:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.existing_collections: List[str] = []

    async def initialize(self) -> bool:
        """Initialize the database with required collections and indexes."""
        try:
            # Get existing collections
            self.existing_collections = await self.db.list_collection_names()
            
            # Create or update collections
            for collection_name, schema in COLLECTIONS.items():
                if collection_name not in self.existing_collections:
                    await self._create_collection(collection_name, schema)
                else:
                    await self._update_collection(collection_name, schema)
            
            logger.info("Database initialization completed successfully")
            return True
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            return False

    async def _create_collection(self, collection_name: str, schema: Dict):
        """Create a new collection with schema validation and indexes."""
        try:
            # Create collection with schema validation
            await self.db.create_collection(
                collection_name,
                validator=schema["validator"]
            )
            
            # Create indexes
            for index in schema["indexes"]:
                await self.db[collection_name].create_index(**index)
            
            logger.info(f"Created collection {collection_name} with schema validation")
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {str(e)}")
            raise

    async def _update_collection(self, collection_name: str, schema: Dict):
        """Update existing collection's schema and indexes if needed."""
        try:
            # Get current collection options
            current_options = await self.db.command({"listCollections": 1, "filter": {"name": collection_name}})
            if not current_options.get("cursor", {}).get("firstBatch"):
                # Collection doesn't exist, create it
                await self._create_collection(collection_name, schema)
                return

            # Get existing indexes
            existing_indexes = await self.db[collection_name].list_indexes().to_list(length=None)
            existing_index_keys = {tuple(sorted(idx["key"].items())) for idx in existing_indexes}
            
            # Only create missing indexes
            for index in schema["indexes"]:
                index_key = tuple(sorted(index["keys"]))
                if index_key not in existing_index_keys:
                    await self.db[collection_name].create_index(**index)
            
            logger.info(f"Collection {collection_name} already exists with correct schema")
        except Exception as e:
            logger.error(f"Failed to update collection {collection_name}: {str(e)}")
            raise

async def init_database(motor_client: AsyncIOMotorClient, db_name: str) -> AsyncIOMotorDatabase:
    """
    Initialize the database with required collections and indexes.
    Returns the database instance if successful, raises exception otherwise.
    """
    try:
        db = motor_client[db_name]
        initializer = DatabaseInitializer(db)
        
        # Get existing collections
        existing_collections = await db.list_collection_names()
        
        # If all required collections exist, just return the db
        if all(collection in existing_collections for collection in COLLECTIONS.keys()):
            logger.info("All required collections exist, connecting to existing database")
            return db
            
        # Otherwise, initialize the database
        if await initializer.initialize():
            return db
        else:
            raise Exception("Database initialization failed")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise

# Usage example:
# async def get_database():
#     client = AsyncIOMotorClient("mongodb://localhost:27017")
#     try:
#         db = await init_database(client, "adhd_coach")
#         return db
#     except Exception as e:
#         logger.error(f"Failed to initialize database: {str(e)}")
#         raise 