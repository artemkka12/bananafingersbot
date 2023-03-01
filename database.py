from pymongo import MongoClient

import settings

cluster = MongoClient(settings.MONGOENGINE_LINK)

db = cluster[settings.MONGOENGINE_DATABASE]
# collection = db[settings.MONGOENGINE_DATABASE]


def create_user(chat_id: int, username: str, is_subscribed: bool) -> None:
    db.users.insert_one({"chat_id": chat_id, "username": username, "is_subscribed": is_subscribed})


def get_user(chat_id: int) -> dict:
    return db.users.find_one({"chat_id": chat_id})


def update_user(chat_id: int, username: str, is_subscribed: bool) -> None:
    db.users.update_one({"chat_id": chat_id}, {"$set": {"username": username, "is_subscribed": is_subscribed}})


def get_all_chats() -> list:
    return [user["chat_id"] for user in db.users.find({})]


def update_or_create_user(chat_id: int, username: str, is_subscribed: bool) -> None:
    try:
        update_user(chat_id, username, is_subscribed)
    except IndexError:
        create_user(chat_id, username, is_subscribed)
