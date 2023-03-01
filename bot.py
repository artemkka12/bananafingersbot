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
from database import update_or_create_user
from helpers import get_categories, get_products

logging.basicConfig(filename="bot.log", level=logging.INFO)

bot = telebot.TeleBot(settings.BOT_TOKEN)
bot.set_my_commands(
    [
        BotCommand("start", "Start the bot."),
        BotCommand("categories", "Select a category."),
        BotCommand("subscribe", "Subscribe to daily notifications about high sales (more than 50%)."),
        BotCommand("unsubscribe", "Unsubscribe from daily notifications."),
    ]
)


@bot.message_handler(commands=["start"])
def start(message: Message) -> None:
    logging.info(
        f"Date: {datetime.now()}, Chat id: {message.chat.id}, "
        f"User {message.from_user.username}, Message: {message.text}"
    )

    text = "Hello! I'm a bot that will help you find the best deals on climbing gear. "
    text += "Type /categories to select a category."

    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=["categories"])
def categories(message: Message) -> None:
    logging.info(
        f"Date: {datetime.now()}, Chat id: {message.chat.id}, "
        f"User {message.from_user.username}, Message: {message.text}"
    )

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    for category in get_categories():
        keyboard.add(KeyboardButton(category))

    bot.send_message(chat_id=message.chat.id, text="Please select a category.", reply_markup=keyboard)
    bot.register_next_step_handler(message, handle_category_choice)


@bot.message_handler(commands=["subscribe"])
def subscribe(message: Message) -> None:
    logging.info(
        f"Date: {datetime.now()}, Chat id: {message.chat.id}, "
        f"User {message.from_user.username}, Message: {message.text}"
    )

    update_or_create_user(message.chat.id, message.from_user.username, True)
    bot.send_message(chat_id=message.chat.id, text="You have been subscribed to daily notifications.")


@bot.message_handler(commands=["unsubscribe"])
def unsubscribe(message: Message) -> None:
    logging.info(
        f"Date: {datetime.now()}, Chat id: {message.chat.id}, "
        f"User {message.from_user.username}, Message: {message.text}"
    )

    update_or_create_user(message.chat.id, message.from_user.username, False)
    bot.send_message(chat_id=message.chat.id, text="You have been unsubscribed from daily notifications.")


# noinspection DuplicatedCode
@bot.callback_query_handler(func=lambda call: call.data.startswith("products"))
def handle_products_pagination(call: CallbackQuery) -> None:
    logging.info(
        f"Date: {datetime.now()}, Chat id: {call.message.chat.id}, "
        f"User {call.message.from_user.username}, Message: {call.message.text}"
    )

    page_number = int(call.data.split("-")[-1])
    start_index = (page_number - 1) * settings.PRODUCTS_PER_PAGE
    end_index = start_index + settings.PRODUCTS_PER_PAGE

    is_notification = "notification" in call.data
    file_path = Path(settings.MEDIA_PATH, f"{'notification_' * is_notification}{call.message.chat.id}.json").as_posix()

    with open(file_path, "r") as f:
        products = json.load(f)

    products_message = "\n".join(
        [
            f"{product['link']}\nPrice: £{product['current_price']}\n"
            f"Old price: £{product['old_price']}\nSale: {product['sale']}%\n"
            for product in products[start_index:end_index]
        ]
    )

    inline_keyboard = InlineKeyboardMarkup(row_width=3)

    if page_number > 1:
        inline_keyboard.add(
            InlineKeyboardButton(
                "<< Prev", callback_data=f"products{'-notification' * is_notification}-{page_number - 1}"
            )
        )
    if end_index < len(products):
        inline_keyboard.add(
            InlineKeyboardButton(
                "Next >>", callback_data=f"products{'-notification' * is_notification}-{page_number + 1}"
            )
        )

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=products_message,
        reply_markup=inline_keyboard,
    )


def handle_category_choice(message: Message) -> None:
    logging.info(
        f"Date: {datetime.now()}, Chat id: {message.chat.id}, "
        f"User {message.from_user.username}, Message: {message.text}"
    )

    if message.text not in get_categories().keys():
        bot.send_message(chat_id=message.chat.id, text="Please select a valid category.")
        bot.register_next_step_handler(message, categories)
        return

    bot.send_message(chat_id=message.chat.id, text="Please enter the minimum sale.")
    bot.register_next_step_handler(message, handle_min_sale, message.text)


def handle_min_sale(message: Message, category_choice) -> None:
    logging.info(
        f"Date: {datetime.now()}, Chat id: {message.chat.id}, "
        f"User {message.from_user.username}, Message: {message.text}"
    )

    min_sale = int(message.text) if message.text.isdigit() else None

    if min_sale and not 0 <= min_sale <= 100:
        bot.send_message(chat_id=message.chat.id, text="Please enter a valid number between 0 and 100.")
        bot.register_next_step_handler(message, handle_min_sale, category_choice)
        return

    bot.send_message(chat_id=message.chat.id, text="Please enter the minimum and maximum price.\nExample: 10 100.")
    bot.register_next_step_handler(message, handle_price_range, category_choice, min_sale)


def handle_price_range(message: Message, category_choice: str, min_sale: int) -> None:
    logging.info(
        f"Date: {datetime.now()}, Chat id: {message.chat.id}, "
        f"User {message.from_user.username}, Message: {message.text}"
    )

    try:
        min_price, max_price = message.text.split()
        min_price = int(min_price) if min_price.isdigit() else None
        max_price = int(max_price) if max_price.isdigit() else None

        if min_price is None or max_price is None or min_price > max_price or min_price < 0 or max_price < 0:
            bot.send_message(chat_id=message.chat.id, text="Please enter a valid price range.")
            bot.register_next_step_handler(message, handle_price_range, category_choice, min_sale)
            return

    except ValueError:
        bot.send_message(chat_id=message.chat.id, text="Please enter a valid price range.")
        bot.register_next_step_handler(message, handle_price_range, category_choice, min_sale)
        return

    show_products(message, category_choice, min_sale, min_price, max_price)


# noinspection DuplicatedCode
def show_products(message: Message, category_choice: str, min_sale: int, min_price: int, max_price: int) -> None:
    logging.info(
        f"Date: {datetime.now()}, Chat id: {message.chat.id}, "
        f"User {message.from_user.username}, Message: {message.text}"
    )

    bot.send_message(
        chat_id=message.chat.id,
        text=f"Category: {category_choice}.\nMinimum sale: {min_sale}%\n"
        f"Price range: £{min_price} - £{max_price}\nStarted to search products.",
        reply_markup=ReplyKeyboardRemove(),
    )

    category_link = get_categories().get(category_choice)
    products = get_products(category_link, min_sale, min_price, max_price)

    if not products:
        bot.send_message(chat_id=message.chat.id, text="No products found.")
        return

    products = sorted(products, key=lambda x: x["sale"], reverse=True)
    file_path = Path(settings.MEDIA_PATH, f"{message.chat.id}.json").as_posix()

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

    if len(products) > settings.PRODUCTS_PER_PAGE:
        inline_keyboard.add(InlineKeyboardButton("Next >>", callback_data="products-page-2"))

    bot.send_message(chat_id=message.chat.id, text=products_message, reply_markup=inline_keyboard)


if __name__ == "__main__":
    logging.info(f"Date: {datetime.now()}, Bot started")
    bot.infinity_polling()
