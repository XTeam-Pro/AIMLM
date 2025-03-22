import logging
from typing import Any

from pymongo import MongoClient

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
client: MongoClient[Any] = MongoClient(settings.MONGO_URL, serverSelectionTimeoutMS=5000)
db = client[settings.MONGO_DB]
products_collection = db["product"]


def init_mongo() -> None:
    """
    Initializes MongoDB.
    """
    try:
        logger.info(f"Connecting to MongoDB at {settings.MONGO_URL}...")
        db.command("ping")  # Проверка доступности
        logger.info("MongoDB connection successful")
        # Создание коллекции с JSON Schema
        db.create_collection("product", validator={
            "$jsonSchema": {
                "bsonType": "object",
                "required": [
                    "title",
                    "category",
                    "price",
                    "rating"
                ],
                "properties": {
                    "title": {
                        "bsonType": "string",
                        "description": "Title of the product"
                    },
                    "category": {
                        "bsonType": "string",
                        "description": "Category of the product"
                    },
                    "price": {
                        "bsonType": "double",
                        "description": "Price of the product"
                    },
                    "rating": {
                        "bsonType": "double",
                        "description": "Rating of the product"
                    }
                }
            }
        })
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
