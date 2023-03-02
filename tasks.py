import json
from pathlib import Path

from celery import Celery
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

import settings
from bot import bot
from database import get_subscribed_users
from helpers import products_on_big_sale

app = Celery("tasks", broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_BROKER_URL)


# noinspection DuplicatedCode
@app.task
def send_daily_notification():
    subscribed_users = get_subscribed_users()
    products = products_on_big_sale()

    if not products:
        return

    products = sorted(products, key=lambda x: x["sale"], reverse=True)
    for user in subscribed_users:
        products_message = "\n".join(
            [
                f"{product['link']}\nPrice: £{product['current_price']}\n"
                f"Old price: £{product['old_price']}\nSale: {product['sale']}%\n"
                for product in products[: settings.PRODUCTS_PER_PAGE]
            ]
        )

        bot.send_message(chat_id=user["chat_id"], text="Daily notification:")

        if len(products) > settings.PRODUCTS_PER_PAGE:
            file_path = Path(settings.MEDIA_PATH, f"notification_{user['chat_id']}.json").as_posix()

            with open(file_path, "w") as f:
                json.dump(products, f, indent=4)

            inline_keyboard = InlineKeyboardMarkup(row_width=3)
            inline_keyboard.add(InlineKeyboardButton("Next >>", callback_data="products-notification-2"))

            bot.send_message(chat_id=user["chat_id"], text=products_message, reply_markup=inline_keyboard)
        else:
            bot.send_message(chat_id=user["chat_id"], text=products_message)


app.conf.beat_schedule = {
    "send-daily-notification": {
        "task": "tasks.send_daily_notification",
        "schedule": 60 * 60 * 24,
    },
}
