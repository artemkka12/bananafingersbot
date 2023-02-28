import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")

MONGOENGINE_LINK = os.getenv("MONGOENGINE_LINK")
MONGOENGINE_DATABASE = os.getenv("MONGOENGINE_DATABASE")

PRODUCTS_PER_PAGE = 5
MEDIA_PATH = "products"
