import json
import logging
from datetime import datetime
from pathlib import Path

import telebot
from telebot.types import (
    BotCommand,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

import settings
from helpers import get_categories, get_products

logging.basicConfig(filename="bot.log", level=logging.INFO)

bot = telebot.TeleBot(settings.BOT_TOKEN)
bot.set_my_commands([BotCommand("start", "Start the bot"), BotCommand("categories", "Select a category")])


@bot.message_handler(commands=["start"])
def handle_start(message: Message) -> None:
    logging.info(
        f"Date: {datetime.now()}, Chat id: {message.chat.id}, "
        f"User {message.from_user.username}, Message: {message.text}, function: handle_start"
    )
    text = "Hello! I'm a bot that will help you find the best deals on climbing gear. "
    text += "Type /categories to select a category."
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=["categories"])
def handle_categories(message: Message) -> None:
    logging.info(
        f"Date: {datetime.now()}, Chat id: {message.chat.id}, "
        f"User {message.from_user.username}, Message: {message.text}, function: handle_categories"
    )
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    for category in get_categories():
        keyboard.add(KeyboardButton(category))

    bot.send_message(chat_id=message.chat.id, text="Please select a category", reply_markup=keyboard)
    bot.register_next_step_handler(message, handle_category_choice)


# noinspection DuplicatedCode
@bot.callback_query_handler(func=lambda call: call.data.startswith("products"))
def handle_products_pagination(call: CallbackQuery) -> None:
    logging.info(
        f"Date: {datetime.now()}, Chat id: {call.message.chat.id}, "
        f"User {call.message.from_user.username}, Message: {call.message.text}, function: handle_products_pagination"
    )
    page_number = int(call.data.split("-")[1])
    start_index = (page_number - 1) * settings.PRODUCTS_PER_PAGE
    end_index = start_index + settings.PRODUCTS_PER_PAGE

    file_path = Path(settings.MEDIA_PATH).joinpath(f"{call.message.chat.id}.json").as_posix()

    with open(file_path, "r") as f:
        products = json.load(f)

    page_products = products[start_index:end_index]

    products_message = [
        f"{product['link']}\nPrice: £{product['current_price']}\n"
        f"Old price: £{product['old_price']}\nSale: {product['sale']}%\n"
        for product in page_products
    ]

    inline_keyboard = InlineKeyboardMarkup(row_width=3)

    if page_number > 1:
        inline_keyboard.add(InlineKeyboardButton("<< Prev", callback_data=f"products-{page_number - 1}"))
    if end_index < len(products):
        inline_keyboard.add(InlineKeyboardButton("Next >>", callback_data=f"products-{page_number + 1}"))

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="\n".join(products_message),
        reply_markup=inline_keyboard,
    )


def handle_category_choice(message: Message) -> None:
    logging.info(
        f"Date: {datetime.now()}, Chat id: {message.chat.id}, "
        f"User {message.from_user.username}, Message: {message.text}, function: handle_category_choice"
    )
    bot.send_message(chat_id=message.chat.id, text="Please enter the minimum sale.")
    bot.register_next_step_handler(message, handle_min_sale, message.text)


def handle_min_sale(message: Message, category_choice) -> None:
    min_sale = int(message.text) if message.text.isdigit() else None
    if min_sale is None or not 0 <= min_sale <= 100:
        bot.send_message(chat_id=message.chat.id, text="Please enter a valid number between 0 and 100.")
        bot.register_next_step_handler(message, handle_min_sale, category_choice)
        return
    bot.send_message(chat_id=message.chat.id, text="Please enter the minimum and maximum price. Example: 10 100")
    bot.register_next_step_handler(message, handle_pagination, category_choice, min_sale)


# noinspection DuplicatedCode
def handle_pagination(message: Message, category_choice: str, min_sale: int) -> None:
    logging.info(
        f"Date: {datetime.now()}, Chat id: {message.chat.id}, "
        f"User {message.from_user.username}, Message: {message.text}, function: handle_pagination"
    )

    min_price, max_price = message.text.split()
    min_price = int(min_price) if min_price.isdigit() else None
    max_price = int(max_price) if max_price.isdigit() else None

    if min_price is None or max_price is None or min_price > max_price or min_price < 0 or max_price < 0:
        bot.send_message(chat_id=message.chat.id, text="Please enter a valid price range.")
        bot.register_next_step_handler(message, handle_pagination, category_choice, min_sale)
        return

    bot.send_message(
        chat_id=message.chat.id,
        text=f"Category: {category_choice}.\nMinimum sale: {min_sale}%\nStarted to search products.",
        reply_markup=ReplyKeyboardRemove(),
    )

    category_link = get_categories().get(category_choice)
    products = get_products(category_link, min_sale, min_price, max_price)

    if not products:
        bot.send_message(chat_id=message.chat.id, text="No products found.")
        return

    products = sorted(products, key=lambda x: x["sale"], reverse=True)

    file_path = Path(settings.MEDIA_PATH).joinpath(f"{message.chat.id}.json").as_posix()

    with open(file_path, "w") as f:
        json.dump(products, f, indent=4)

    page_number = int(message.text.split()[1]) if len(message.text.split()) > 1 else 1
    start_index = (page_number - 1) * settings.PRODUCTS_PER_PAGE
    end_index = start_index + settings.PRODUCTS_PER_PAGE

    products_message = []

    for product in products[start_index:end_index]:
        products_message.append(
            f"{product['link']}\nPrice: £{product['current_price']}\n"
            f"Old price: £{product['old_price']}\nSale : {product['sale']}%\n"
        )

    inline_keyboard = InlineKeyboardMarkup(row_width=3)

    if page_number > 1:
        inline_keyboard.add(InlineKeyboardButton("<< Prev", callback_data=f"products-{page_number - 1}"))
    if end_index < len(products):
        inline_keyboard.add(InlineKeyboardButton("Next >>", callback_data=f"products-{page_number + 1}"))

    bot.send_message(chat_id=message.chat.id, text="\n".join(products_message), reply_markup=inline_keyboard)


if __name__ == "__main__":
    logging.info(f"Date: {datetime.now()}, Bot started")
    bot.infinity_polling()
