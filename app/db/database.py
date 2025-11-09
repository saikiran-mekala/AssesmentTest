import os
from pymongo import MongoClient


def get_database():
    mongo_url = os.getenv("MONGO_URL", "mongodb://mongo:27017")
    db_name = os.getenv("DB_NAME", "reminder_dev")
    client = MongoClient(mongo_url)
    return client[db_name]