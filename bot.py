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

import database as db
import helpers
import settings

logging.basicConfig(filename="bot.log", level=logging.INFO)

bot = telebot.TeleBot(settings.BOT_TOKEN)
bot.set_my_commands(
    [
        BotCommand("start", "Start the bot"),
        BotCommand("categories", "Select a category"),
        BotCommand("subscribe", "Subscribe to daily notifications about high sales"),
        BotCommand("unsubscribe", "Unsubscribe from daily notifications about high sales"),
    ]
)


@bot.message_handler(commands=["start"])
def handle_start(message: Message) -> None:
    """Start the bot"""
    logging.info(
        f"Date: {datetime.now()}, Chat id: {message.chat.id}, "
        f"User {message.from_user.username}, Message: {message.text}, function: handle_start"
    )

    text = "Hello! I'm a bot that will help you find the best deals on climbing gear. "
    text += "Type /categories to select a category."

    db.create_user(message.chat.id, message.from_user.username, False)
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=["categories"])
def handle_categories(message: Message) -> None:
    """Select a category"""
    logging.info(
        f"Date: {datetime.now()}, Chat id: {message.chat.id}, "
        f"User {message.from_user.username}, Message: {message.text}, function: handle_categories"
    )

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    for category in helpers.get_categories():
        keyboard.add(KeyboardButton(category))

    bot.send_message(chat_id=message.chat.id, text="Please select a category", reply_markup=keyboard)
    bot.register_next_step_handler(message, handle_category_choice)


@bot.message_handler(commands=["subscribe"])
def handle_subscribe(message: Message) -> None:
    """Subscribe to daily notifications"""
    logging.info(
        f"Date: {datetime.now()}, Chat id: {message.chat.id}, "
        f"User {message.from_user.username}, Message: {message.text}, function: handle_subscribe"
    )

    db.update_user(message.chat.id, message.from_user.username, True)
    bot.send_message(chat_id=message.chat.id, text="You have been subscribed to daily notifications.")


@bot.message_handler(commands=["unsubscribe"])
def handle_unsubscribe(message: Message) -> None:
    """Unsubscribe from daily notifications"""
    logging.info(
        f"Date: {datetime.now()}, Chat id: {message.chat.id}, "
        f"User {message.from_user.username}, Message: {message.text}, function: handle_unsubscribe"
    )

    db.update_user(message.chat.id, message.from_user.username, False)
    bot.send_message(chat_id=message.chat.id, text="You have been unsubscribed from daily notifications.")


# noinspection DuplicatedCode
@bot.callback_query_handler(func=lambda call: call.data.startswith("products"))
def handle_products_pagination(call: CallbackQuery) -> None:
    """Handle products pagination"""
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

    products_message = "\n".join(
        [
            f"{product['link']}\nPrice: £{product['current_price']}\n"
            f"Old price: £{product['old_price']}\nSale: {product['sale']}%\n"
            for product in products[start_index:end_index]
        ]
    )

    inline_keyboard = InlineKeyboardMarkup(row_width=3)

    if page_number > 1:
        inline_keyboard.add(InlineKeyboardButton("<< Prev", callback_data=f"products-{page_number - 1}"))
    if end_index < len(products):
        inline_keyboard.add(InlineKeyboardButton("Next >>", callback_data=f"products-{page_number + 1}"))

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=products_message,
        reply_markup=inline_keyboard,
    )


def handle_category_choice(message: Message) -> None:
    """Handle category choice"""
    category_choice = message.text
    logging.info(
        f"Date: {datetime.now()}, Chat id: {message.chat.id}, "
        f"User {message.from_user.username}, Message: {category_choice}, function: handle_category_choice"
    )

    if category_choice not in helpers.get_categories().keys():
        bot.send_message(chat_id=message.chat.id, text="Please select a valid category.")
        bot.register_next_step_handler(message, handle_categories)
        return

    bot.send_message(chat_id=message.chat.id, text="Please enter the minimum sale.")
    bot.register_next_step_handler(message, handle_min_sale, message.text)


def handle_min_sale(message: Message, category_choice) -> None:
    """Handle minimum sale"""
    min_sale = int(message.text) if message.text.isdigit() else None

    if min_sale is None or not 0 <= min_sale <= 100:
        bot.send_message(chat_id=message.chat.id, text="Please enter a valid number between 0 and 100.")
        bot.register_next_step_handler(message, handle_min_sale, category_choice)
        return

    bot.send_message(chat_id=message.chat.id, text="Please enter the minimum and maximum price. Example: 10 100")
    bot.register_next_step_handler(message, handle_price_range, category_choice, min_sale)


def handle_price_range(message: Message, category_choice: str, min_sale: int) -> None:
    """Handle price range"""
    try:
        min_price, max_price = message.text.split()
        min_price = int(min_price) if min_price.isdigit() else None
        max_price = int(max_price) if max_price.isdigit() else None
    except ValueError:
        bot.send_message(chat_id=message.chat.id, text="Please enter a valid price range.")
        bot.register_next_step_handler(message, handle_price_range, category_choice, min_sale)
        return

    if min_price is None or max_price is None or min_price > max_price or min_price < 0 or max_price < 0:
        bot.send_message(chat_id=message.chat.id, text="Please enter a valid price range.")
        bot.register_next_step_handler(message, handle_price_range, category_choice, min_sale)
        return

    show_products(message, category_choice, min_sale, min_price, max_price)


# noinspection DuplicatedCode
def show_products(message: Message, category_choice: str, min_sale: int, min_price: int, max_price: int) -> None:
    """Show products"""
    logging.info(
        f"Date: {datetime.now()}, Chat id: {message.chat.id}, "
        f"User {message.from_user.username}, Message: {message.text}, function: show_products"
    )

    bot.send_message(
        chat_id=message.chat.id,
        text=f"Category: {category_choice}.\nMinimum sale: {min_sale}%\n"
        f"Price range: £{min_price} - £{max_price}\nStarted to search products.",
        reply_markup=ReplyKeyboardRemove(),
    )

    category_link = helpers.get_categories().get(category_choice)
    products = helpers.get_products(category_link, min_sale, min_price, max_price)

    if not products:
        bot.send_message(chat_id=message.chat.id, text="No products found.")
        return

    products = sorted(products, key=lambda x: x["sale"], reverse=True)

    file_path = Path(settings.MEDIA_PATH).joinpath(f"{message.chat.id}.json").as_posix()

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

    bot.send_message(chat_id=message.chat.id, text=products_message, reply_markup=inline_keyboard)


if __name__ == "__main__":
    logging.info(f"Date: {datetime.now()}, Bot started")
    bot.infinity_polling()
