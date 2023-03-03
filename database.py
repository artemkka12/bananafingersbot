from pymongo import MongoClient

import settings

client = MongoClient(settings.MONGOENGINE_LINK)
db = client[settings.MONGOENGINE_DATABASE]
collection = db[settings.MONGOENGINE_COLLECTION]


def create_user(**kwargs) -> None:
    collection.insert_one(kwargs)


def get_user(chat_id: int) -> dict:
    return collection.find_one({"chat_id": chat_id})


def update_user(chat_id: int, **kwargs) -> None:
    collection.update_one({"chat_id": chat_id}, {"$set": {**kwargs}})


def get_subscribed_users() -> list:
    return [user for user in collection.find({"is_subscribed": True})]


def update_or_create_user(**kwargs) -> None:
    if get_user(kwargs.get("chat_id")):
        update_user(**kwargs)
    else:
        create_user(**kwargs)
