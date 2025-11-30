from pymongo import MongoClient
from config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    client: MongoClient = None
    db = None

def connect_db():
    """Connect to MongoDB"""
    try:
        Database.client = MongoClient(settings.MONGO_URL)
        Database.db = Database.client[settings.DB_NAME]
        # Test connection
        Database.client.server_info()
        logger.info(f"Successfully connected to MongoDB: {settings.DB_NAME}")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

def close_db():
    """Close MongoDB connection"""
    if Database.client:
        Database.client.close()
        logger.info("MongoDB connection closed")

def get_db():
    """Get database instance"""
    if Database.db is None:
        connect_db()
    return Database.db