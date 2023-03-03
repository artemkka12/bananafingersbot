import json
import logging
from datetime import datetime
from pathlib import Path

import telebot
from deep_translator import GoogleTranslator
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
from database import get_user, update_or_create_user
from helpers import get_categories, get_products, get_products_message

logging.basicConfig(filename="bot.log", level=logging.INFO)

bot = telebot.TeleBot(settings.BOT_TOKEN)
bot.set_my_commands(
    [
        BotCommand("start", "Start the bot."),
        BotCommand("categories", "Select a category."),
        BotCommand("subscribe", "Subscribe to daily notification about high sales (more than 50%)."),
        BotCommand("unsubscribe", "Unsubscribe from daily notification."),
        BotCommand("set_language", "Set the language of the bot."),
    ]
)


@bot.message_handler(commands=["start"])
def start(message: Message) -> None:
    logging.info(
        f"Date: {datetime.now()}, Chat id: {message.chat.id}, "
        f"User {message.from_user.username}, Message: {message.text}"
    )

    lang = get_user(message.chat.id).get("language", message.from_user.language_code)
    text = "Hello! I'm a bot that will help you find the best deals on climbing gear. "
    text += "Type /categories to select a category."
    text = GoogleTranslator("auto", lang).translate(text)

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

    lang = get_user(message.chat.id).get("language", message.from_user.language_code)
    text = GoogleTranslator("auto", lang).translate("Please select a category.")

    bot.send_message(chat_id=message.chat.id, text=text, reply_markup=keyboard)
    bot.register_next_step_handler(message, handle_category_choice)


@bot.message_handler(commands=["subscribe"])
def subscribe(message: Message) -> None:
    logging.info(
        f"Date: {datetime.now()}, Chat id: {message.chat.id}, "
        f"User {message.from_user.username}, Message: {message.text}"
    )

    update_or_create_user(chat_id=message.chat.id, username=message.from_user.username, is_subscribed=True)

    lang = get_user(message.chat.id).get("language", message.from_user.language_code)
    text = GoogleTranslator("auto", lang).translate("You have been subscribed to daily notification.")

    bot.send_message(chat_id=message.chat.id, text=text)


@bot.message_handler(commands=["unsubscribe"])
def unsubscribe(message: Message) -> None:
    logging.info(
        f"Date: {datetime.now()}, Chat id: {message.chat.id}, "
        f"User {message.from_user.username}, Message: {message.text}"
    )

    update_or_create_user(chat_id=message.chat.id, username=message.from_user.username, is_subscribed=False)

    lang = get_user(message.chat.id).get("language", message.from_user.language_code)
    text = GoogleTranslator("auto", lang).translate("You have been unsubscribed from daily notification.")

    bot.send_message(chat_id=message.chat.id, text=text)


@bot.message_handler(commands=["set_language"])
def set_language(message: Message) -> None:
    logging.info(
        f"Date: {datetime.now()}, Chat id: {message.chat.id}, "
        f"User {message.from_user.username}, Message: {message.text}"
    )

    keyboard = InlineKeyboardMarkup()

    for language in settings.LANGUAGES:
        keyboard.add(InlineKeyboardButton(language, callback_data=f"language-{language}"))

    lang = get_user(message.chat.id).get("language", message.from_user.language_code)
    text = GoogleTranslator("auto", lang).translate("Please select a language.")

    bot.send_message(chat_id=message.chat.id, text=text, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith("language"))
def handle_language_choice(call: CallbackQuery) -> None:
    logging.info(
        f"Date: {datetime.now()}, Chat id: {call.message.chat.id}, "
        f"User {call.message.from_user.username}, Message: {call.message.text}"
    )

    lang = get_user(call.message.chat.id).get("language", call.message.from_user.language_code)

    language = call.data.split("-")[-1]

    if language not in settings.LANGUAGES:
        bot.answer_callback_query(call.id, GoogleTranslator("auto", lang).translate("Invalid language."))
        return

    update_or_create_user(chat_id=call.message.chat.id, username=call.message.from_user.username, language=language)
    bot.answer_callback_query(call.id, GoogleTranslator("auto", language).translate("Language updated."))


# noinspection DuplicatedCode
@bot.callback_query_handler(func=lambda call: call.data.startswith("products"))
def handle_products_pagination(call: CallbackQuery) -> None:
    logging.info(
        f"Date: {datetime.now()}, Chat id: {call.message.chat.id}, "
        f"User {call.message.from_user.username}, Message: {call.message.text}"
    )

    lang = get_user(call.message.chat.id).get("language", call.message.from_user.language_code)

    page_number = int(call.data.split("-")[-1])
    start_index = (page_number - 1) * settings.PRODUCTS_PER_PAGE
    end_index = start_index + settings.PRODUCTS_PER_PAGE

    is_notification = "notification" in call.data
    file_path = Path(settings.MEDIA_PATH, f"{'notification_' * is_notification}{call.message.chat.id}.json").as_posix()

    with open(file_path, "r") as f:
        products = json.load(f)

    products_message = get_products_message(products[start_index:end_index], lang)

    inline_keyboard = InlineKeyboardMarkup(row_width=3)

    if page_number > 1:
        inline_keyboard.add(
            InlineKeyboardButton("<<", callback_data=f"products{'-notification' * is_notification}-{page_number - 1}")
        )
    if end_index < len(products):
        inline_keyboard.add(
            InlineKeyboardButton(">>", callback_data=f"products{'-notification' * is_notification}-{page_number + 1}")
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

    lang = get_user(message.chat.id).get("language", message.from_user.language_code)

    if message.text not in get_categories().keys():
        bot.send_message(message.chat.id, GoogleTranslator("auto", lang).translate("Invalid category."))
        bot.register_next_step_handler(message, categories)
        return

    bot.send_message(message.chat.id, GoogleTranslator("auto", lang).translate("Please enter the minimum sale."))
    bot.register_next_step_handler(message, handle_min_sale, message.text)


def handle_min_sale(message: Message, category_choice) -> None:
    logging.info(
        f"Date: {datetime.now()}, Chat id: {message.chat.id}, "
        f"User {message.from_user.username}, Message: {message.text}"
    )

    lang = get_user(message.chat.id).get("language", message.from_user.language_code)

    min_sale = int(message.text) if message.text.isdigit() else None

    if min_sale and not 0 <= min_sale <= 100:
        bot.send_message(message.chat.id, GoogleTranslator("auto", lang).translate("Invalid minimum sale."))
        bot.register_next_step_handler(message, handle_min_sale, category_choice)
        return

    bot.send_message(message.chat.id, GoogleTranslator("auto", lang).translate("Please enter the price range. (1 10)"))
    bot.register_next_step_handler(message, handle_price_range, category_choice, min_sale)


def handle_price_range(message: Message, category_choice: str, min_sale: int) -> None:
    logging.info(
        f"Date: {datetime.now()}, Chat id: {message.chat.id}, "
        f"User {message.from_user.username}, Message: {message.text}"
    )

    lang = get_user(message.chat.id).get("language", message.from_user.language_code)

    try:
        min_price, max_price = message.text.split()
        min_price = int(min_price) if min_price.isdigit() else None
        max_price = int(max_price) if max_price.isdigit() else None

        if min_price is None or max_price is None or min_price > max_price or min_price < 0 or max_price < 0:
            bot.send_message(message.chat.id, GoogleTranslator("auto", lang).translate("Invalid price range."))
            bot.register_next_step_handler(message, handle_price_range, category_choice, min_sale)
            return

    except ValueError:
        bot.send_message(message.chat.id, GoogleTranslator("auto", lang).translate("Invalid price range."))
        bot.register_next_step_handler(message, handle_price_range, category_choice, min_sale)
        return

    show_products(message, category_choice, min_sale, min_price, max_price)


# noinspection DuplicatedCode
def show_products(message: Message, category_choice: str, min_sale: int, min_price: int, max_price: int) -> None:
    logging.info(
        f"Date: {datetime.now()}, Chat id: {message.chat.id}, "
        f"User {message.from_user.username}, Message: {message.text}"
    )

    lang = get_user(message.chat.id).get("language", message.from_user.language_code)

    bot.send_message(
        chat_id=message.chat.id,
        text=GoogleTranslator("auto", lang).translate("Please wait..."),
        reply_markup=ReplyKeyboardRemove(),
    )

    category_link = get_categories().get(category_choice)
    products = get_products(category_link, min_sale, min_price, max_price)

    if not products:
        bot.send_message(chat_id=message.chat.id, text=GoogleTranslator("auto", lang).translate("No products found."))
        return

    products = sorted(products, key=lambda x: x["sale"], reverse=True)

    products_message = get_products_message(products[: settings.PRODUCTS_PER_PAGE], lang)

    if len(products) > settings.PRODUCTS_PER_PAGE:
        file_path = Path(settings.MEDIA_PATH, f"{message.chat.id}.json").as_posix()

        with open(file_path, "w") as f:
            json.dump(products, f, indent=4)

        inline_keyboard = InlineKeyboardMarkup(row_width=3)
        inline_keyboard.add(InlineKeyboardButton(">>", callback_data="products-page-2"))

        bot.send_message(chat_id=message.chat.id, text=products_message, reply_markup=inline_keyboard)
    else:
        bot.send_message(chat_id=message.chat.id, text=products_message)


if __name__ == "__main__":
    logging.info(f"Date: {datetime.now()}, Bot started")
    bot.infinity_polling()
