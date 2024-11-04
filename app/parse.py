import csv
from dataclasses import dataclass, astuple, fields
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

PAGES_URL = {
    "computers": urljoin(HOME_URL, "computers/"),
    "laptops": urljoin(HOME_URL, "computers/laptops/"),   #more btn
    "tablets": urljoin(HOME_URL, "computers/tablets/"),   #more btn
    "phones": urljoin(HOME_URL, "phones/"),
    "touch": urljoin(HOME_URL, "phones/touch/")    #more btn
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def init_driver(headless: bool = True) -> webdriver.Chrome:
    options = Options()
    options.headless = headless
    return webdriver.Chrome(options=options)


def parse_single_product(prod_soup: Tag) -> Product:
    return Product(
        title=prod_soup.select_one(".title")["title"],
        description=prod_soup.select_one(".description").text,
        price=float(prod_soup.select_one(".price").text.replace("$", "")),
        rating=int(prod_soup.select_one("p[data-rating]")["data-rating"]),
        num_of_reviews=int(prod_soup.select_one(".review-count").text.split()[0])
    )


def get_products(driver: webdriver.Chrome, url: str) -> list:
    driver.get(url)
    accept_cookies(driver)

    while True:
        try:
            button = driver.find_element(By.CLASS_NAME, "ecomerce-items-scroll-more")
            WebDriverWait(driver, 10).until(ec.element_to_be_clickable(button)).click()
            WebDriverWait(driver,10).until(ec.presence_of_all_elements_located((By.CLASS_NAME, "card-body")))
        except NoSuchElementException:
            break
        except TimeoutException:
            break

    soup = BeautifulSoup(driver.page_source, "html.parser")

    return [
        parse_single_product(prod_soup=product)
        for product in soup.select(".thumbnail")
    ]


def write_products_to_file(products: list[Product], path: str) -> None:
    with open(f"{path}.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([field.name for field in fields(Product)])
        writer.writerows([astuple(product) for product in products])


def accept_cookies(driver: webdriver.Chrome) -> None:
    try:
        cookies_btn = driver.find_element(By.CLASS_NAME, "acceptCookies")
        if cookies_btn.is_displayed():
            cookies_btn.click()
    except NoSuchElementException:
        pass


def get_all_products() -> None:
    driver = init_driver()
    for category, url in PAGES_URL.items():
        print(f"Scraping category: {category}")
        products = get_products(driver, url)
        write_products_to_file(products, category)
        print(f"Saved {len(products)} products to {category}.csv")
    driver.quit()


if __name__ == "__main__":
    get_all_products()

