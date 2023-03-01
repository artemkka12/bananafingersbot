import logging
from itertools import count

import requests
from bs4 import BeautifulSoup

logging.basicConfig(filename="bot.log", level=logging.INFO)


def get_categories() -> dict:
    categories = {}

    response = requests.get("https://bananafingers.co.uk/")
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for category in soup.find_all("li", class_="level-top"):
        category_name = category.find("a").text.strip()
        category_link = category.find("a")["href"]
        categories[category_name] = category_link

    return categories


def get_products(category_link: str, min_sale: int, min_price: int = None, max_price: int = None) -> list:
    products = []

    for i in count(1):
        response = requests.get(category_link + f"?p={i - 1}")
        response.raise_for_status()

        if "t find products matching the selection." in response.text:
            break

        soup = BeautifulSoup(response.text, "html.parser")

        for product in soup.find_all("li", class_="item product product-item"):
            product_link = product.find("a", class_="product-item-link")["href"]

            try:
                if product.find("div", class_="stock unavailable").text:
                    continue
            except AttributeError:
                pass
            try:
                current_price = float(product.find("span", class_="price").text[1:])
            except AttributeError:
                current_price = None
            try:
                old_price = float(product.find("span", class_="old-price").text.strip()[1:])
            except AttributeError:
                old_price = None

            if all([product_link, current_price, old_price]):
                sale = ((old_price - current_price) / old_price) * 100
                if sale >= min_sale and (all([min_price, max_price]) and min_price <= current_price <= max_price):
                    products.append(
                        {
                            "link": product_link,
                            "current_price": current_price,
                            "old_price": old_price,
                            "sale": round(sale),
                        }
                    )

    return products


def products_on_big_sale() -> list:
    categories = get_categories()

    products = []

    for category_name, category_link in categories.items():
        products.extend(get_products(category_link, 50))

    return products
