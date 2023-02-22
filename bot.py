import json
import logging
import os
from datetime import datetime

import telebot
from dotenv import load_dotenv
from telebot.types import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from helpers import get_categories, get_products

load_dotenv()
logging.basicConfig(filename="bot.log", level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
PRODUCTS_PER_PAGE = 5

bot = telebot.TeleBot(BOT_TOKEN)

bot.set_my_commands([BotCommand("start", "Start the bot"), BotCommand("categories", "Select a category")])


@bot.message_handler(commands=["start"])
def handle_start(message):
    logging.info(
        f"Chat id = {message.chat.id}, time = {datetime.now()}, username = {message.from_user.username}, "
        f"function = handle_start, data = {message.text}"
    )
    text = "Hello! I'm a bot that will help you find the best deals on climbing gear. "
    text += "Type /categories to select a category."
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=["categories"])
def handle_categories(message):
    logging.info(
        f"Chat id = {message.chat.id}, time = {datetime.now()}, username = {message.from_user.username}, "
        f"function = handle_categories, data = {message.text}"
    )
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    for category in get_categories(chat_id=message.chat.id):
        keyboard.add(KeyboardButton(category))

    bot.send_message(chat_id=message.chat.id, text="Please select a category", reply_markup=keyboard)
    bot.register_next_step_handler(message, handle_category_choice)


# noinspection DuplicatedCode
@bot.callback_query_handler(func=lambda call: call.data.startswith("products"))
def handle_products_pagination(call):
    logging.info(
        f"Chat id = {call.message.chat.id}, time = {datetime.now()}, username = {call.message.from_user.username}, "
        f"function = handle_products_pagination, data = {call.data}"
    )
    page_number = int(call.data.split("-")[1])
    start_index = (page_number - 1) * PRODUCTS_PER_PAGE
    end_index = start_index + PRODUCTS_PER_PAGE

    with open(f"products/products_{call.message.chat.id}.json", "r") as f:
        products = json.load(f)

    page_products = products[start_index:end_index]

    products_message = [
        f"{product['link']}\nPrice: £{product['current_price']}\nOld price: £{product['old_price']}\n"
        f"Sale: {product['sale']}%\n"
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


def handle_category_choice(message):
    logging.info(
        f"Chat id = {message.chat.id}, time = {datetime.now()}, username = {message.from_user.username}, "
        f"function = handle_category_choice, data = {message.text}"
    )
    category_choice = message.text
    bot.send_message(
        chat_id=message.chat.id, text=f"You have selected {category_choice}. Please enter the minimum sale."
    )
    bot.register_next_step_handler(message, handle_pagination, category_choice)


# noinspection DuplicatedCode
def handle_pagination(message, category_choice):
    logging.info(
        f"Chat id = {message.chat.id}, time = {datetime.now()}, username = {message.from_user.username}, "
        f"function = handle_pagination, data = {message.text}"
    )
    min_sale = int(message.text) if message.text.isdigit() else None

    if min_sale is None or not 0 <= min_sale <= 100:
        bot.send_message(chat_id=message.chat.id, text="Please enter a valid number between 0 and 100.")
        bot.register_next_step_handler(message, handle_pagination, category_choice)
        return

    bot.send_message(
        chat_id=message.chat.id,
        text=f"Minimum sale: {min_sale}%\nStarted to search products.",
        reply_markup=ReplyKeyboardRemove(),
    )

    category_link = get_categories(chat_id=message.chat.id)[category_choice]
    products = get_products(category_link, min_sale, message.chat.id)

    if not products:
        bot.send_message(chat_id=message.chat.id, text="No products found.")
        return

    products = sorted(products, key=lambda x: x["sale"], reverse=True)

    with open(f"products/products_{message.chat.id}.json", "w") as f:
        json.dump(products, f, indent=4)

    product_strings = []
    for product in products:
        product_strings.append(
            f"{product['link']}\nPrice: £{product['current_price']}\n"
            f"Old price: £{product['old_price']}\nSale : {product['sale']}%\n"
        )

    page_number = int(message.text.split()[1]) if len(message.text.split()) > 1 else 1

    start_index = (page_number - 1) * PRODUCTS_PER_PAGE
    end_index = start_index + PRODUCTS_PER_PAGE

    products_message = "\n".join(product_strings[start_index:end_index])
    inline_keyboard = InlineKeyboardMarkup(row_width=3)

    if page_number > 1:
        inline_keyboard.add(InlineKeyboardButton("<< Prev", callback_data=f"products-{page_number - 1}"))
    if end_index < len(products):
        inline_keyboard.add(InlineKeyboardButton("Next >>", callback_data=f"products-{page_number + 1}"))

    bot.send_message(chat_id=message.chat.id, text=products_message, reply_markup=inline_keyboard)


if __name__ == "__main__":
    logging.info(f"Bot started - {datetime.now()}")
    bot.infinity_polling()
