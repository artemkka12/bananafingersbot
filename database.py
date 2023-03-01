from pymongo import MongoClient

import settings

client = MongoClient(settings.MONGOENGINE_LINK)
db = client[settings.MONGOENGINE_DATABASE]
collection = db[settings.MONGOENGINE_COLLECTION]


def create_user(chat_id: int, username: str, is_subscribed: bool) -> None:
    collection.insert_one({"chat_id": chat_id, "username": username, "is_subscribed": is_subscribed})


def get_user(chat_id: int) -> dict:
    return collection.find_one({"chat_id": chat_id})


def update_user(chat_id: int, username: str, is_subscribed: bool) -> None:
    collection.update_one({"chat_id": chat_id}, {"$set": {"username": username, "is_subscribed": is_subscribed}})


def get_subscribed_users() -> list:
    return [user for user in collection.find({"is_subscribed": True})]


def update_or_create_user(chat_id: int, username: str, is_subscribed: bool) -> None:
    if get_user(chat_id):
        update_user(chat_id, username, is_subscribed)
    else:
        create_user(chat_id, username, is_subscribed)
