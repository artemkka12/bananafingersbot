import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
PRODUCTS_PER_PAGE = 5
MEDIA_PATH = "products"
