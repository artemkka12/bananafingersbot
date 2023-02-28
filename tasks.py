import json
from pathlib import Path

from celery import Celery
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

import database
import helpers
import settings
from bot import bot

app = Celery("tasks", broker=settings.CELERY_BROKER_URL)


@app.task
def send_daily_notification():
    chats = database.get_all_chats()
    products = helpers.get_products_with_big_sale()
    print("Products: ", products)
    if not products:
        print("No products with big sale")
        return

    products = sorted(products, key=lambda x: x["sale"], reverse=True)

    for chat_id in chats:
        file_path = Path(settings.MEDIA_PATH).joinpath(f"{chat_id}.json").as_posix()
        with open(file_path, "w") as f:
            json.dump(products, f, indent=4)

        products_message = "\n".join(
            [
                f"{product['link']}\nPrice: £{product['current_price']}\n"
                f"Old price: £{product['old_price']}\nSale: {product['sale']}%\n"
                for product in products[: settings.PRODUCTS_PER_PAGE]
            ]
        )

        inline_keyboard = InlineKeyboardMarkup(row_width=3)
        inline_keyboard.add(InlineKeyboardButton("Next >>", callback_data="products-2"))

        bot.send_message(chat_id=chat_id, text=products_message, reply_markup=inline_keyboard)


app.conf.beat_schedule = {
    "send-daily-notification": {
        "task": "tasks.send_daily_notification",
        "schedule": 60.0 * 60.0 * 24.0,
    },
}
