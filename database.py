from pymongo import MongoClient

import settings

cluster = MongoClient(settings.MONGOENGINE_LINK)

db = cluster[settings.MONGOENGINE_DATABASE]
collection = db[settings.MONGOENGINE_DATABASE]


def create_user(chat_id: int, username: str, is_subscribed: bool) -> None:
    """Save user to database"""
    collection.insert_one({"chat_id": chat_id, "username": username, "is_subscribed": is_subscribed})


def get_user(chat_id: int) -> dict:
    """Get user from database"""
    return collection.find({"chat_id": chat_id})[0]


def update_user(chat_id: int, username: str, is_subscribed: bool) -> None:
    """Update user in database"""
    collection.update_one({"chat_id": chat_id}, {"$set": {"username": username, "is_subscribed": is_subscribed}})


def get_all_chats() -> list:
    """Get all chats from database"""
    return [user["chat_id"] for user in collection.find({})]
