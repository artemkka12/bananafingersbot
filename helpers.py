import logging
from datetime import datetime
from itertools import count

import requests
from bs4 import BeautifulSoup

logging.basicConfig(filename="bot.log", level=logging.INFO)


def get_categories(chat_id: int) -> dict:
    logging.info(f"Chat id = {chat_id}, time = {datetime.now()}, function = get_categories")
    categories = {}

    response = requests.get("https://bananafingers.co.uk/")
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for category in soup.find_all("li", class_="level-top"):
        category_name = category.find("a").text.strip().lower()
        category_link = category.find("a")["href"]
        categories[category_name] = category_link

    return categories


def get_products(category_link: str, min_sale: int, chat_id: int) -> list:
    products = []

    for i in count(1):
        response = requests.get(category_link + f"?p={i - 1}")
        response.raise_for_status()
        logging.info(f"Chat id = {chat_id}, time = {datetime.now()}, page {i} loaded")

        if "t find products matching the selection." in str(response.text):
            logging.info(f"Chat id = {chat_id}, time = {datetime.now()}, no more products")
            break

        soup = BeautifulSoup(response.text, "html.parser")

        for product in soup.find_all("div", class_="product details product-item-details"):
            product_link = product.find("a", class_="product-item-link")["href"]

            try:
                product_current_price = float(product.find("span", class_="price").text[1:])
            except AttributeError:
                product_current_price = None
            try:
                product_old_price = float(product.find("span", class_="old-price").text.strip()[1:])
            except AttributeError:
                product_old_price = None

            if all([product_link, product_current_price, product_old_price]):
                sale = ((product_old_price - product_current_price) / product_old_price) * 100
                if sale >= min_sale:
                    products.append(
                        {
                            "link": product_link,
                            "current_price": product_current_price,
                            "old_price": product_old_price,
                            "sale": round(sale),
                        }
                    )

    return products
