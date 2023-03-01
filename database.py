from pymongo import MongoClient

import settings

cluster = MongoClient(settings.MONGOENGINE_LINK)
db = cluster[settings.MONGOENGINE_DATABASE]
collection = db[settings.MONGOENGINE_COLLECTION]


def create_user(chat_id: int, username: str, is_subscribed: bool) -> None:
    collection.insert_one({"chat_id": chat_id, "username": username, "is_subscribed": is_subscribed})


def get_user(chat_id: int) -> dict:
    return collection.find_one({"chat_id": chat_id})


def update_user(chat_id: int, username: str, is_subscribed: bool) -> None:
    collection.update_one({"chat_id": chat_id}, {"$set": {"username": username, "is_subscribed": is_subscribed}})


def get_all_chats() -> list:
    return [user["chat_id"] for user in collection.find()]


def update_or_create_user(chat_id: int, username: str, is_subscribed: bool) -> None:
    if get_user(chat_id):
        update_user(chat_id, username, is_subscribed)
    else:
        create_user(chat_id, username, is_subscribed)
