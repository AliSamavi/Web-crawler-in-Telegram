import os
import peewee
import pandas as pd
import requests
import xmltodict
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from pyrogram.types import InlineKeyboardButton
import concurrent

DB = peewee.SqliteDatabase("./app/database.sqlite3")
DB.connect()


class Base(peewee.Model):
    class Meta:
        database = DB


class MyShop(Base):
    id = peewee.CharField()
    domain = peewee.CharField()
    token = peewee.CharField()


DB.create_tables([MyShop])


class Control:
    def check_exists(user_id):
        query = MyShop.select().where(MyShop.id == user_id)
        return query.exists()

    def save_domain_token(user_id, domain, token):
        try:
            url = f"https://{domain}/api/?ws_key={token}"
            response = requests.get(url)
            if response.status_code == 200:
                MyShop.create(id=user_id, domain=domain, token=token)
                return "با موفقیت دامنه و توکن ثبت شد.\nاگر قصد دارید وارد پنل کنترل ربات شوید /start را بزنید."
            else:
                return "توکن وارد شده صحیح نمی باشد لطفا دوباره تلاش کنید."
        except:
            return "دامنه وارد شده صحیح نمی باشد لطفا دوباره تلاش کنید."

    def btn_maker(i):
        btn_list = []
        for file in os.listdir("./app/data"):
            name = file.split(".")[0]
            btn_list.append([InlineKeyboardButton(name, f"{i}{file}")])
        btn_list.append([InlineKeyboardButton("برگشت", "home")])
        return btn_list

    def btn_action(self, data):
        i, data = data[0], data[1:]
        data = data.split('@')
        link = pd.read_csv(f"./app/data/{data[0]}")

        if i == "a":
            self.update(link, data)
        elif i == "h":
            HtmlTable(link, data).to_html()

    def update(self, link, data):
        with concurrent.futures.ThreadPoolExecutor(max_workers=int(data[1])) as executor:
            futures = []
            for ID, URL, PSelector, DPSelector in zip(link["ID"], link["URL"], link["Price Selector"], link["Discount Price Selector"]):
                executor.submit(self.process, ID, URL, PSelector, DPSelector)

    def process(self, ID, URL, PSelector, DPSelector):
        C = WebScraper(URL, PSelector, DPSelector)
        Admin().product_update(ID, C.price)


class HtmlTable:
    def __init__(self, link, data):
        self.data = link
        self.max_workers = int(data[1])
        self.html_table = '<style>table{margin:0 auto}thead{background-color:#acffaf}table,th,td{border-collapse:collapse;padding:5px 15px;text-align:center;border-color:black}</style>'
        self.html_table += "<table border=\"1\">\n"
        self.html_table += "<thead><tr><th>نام</th><th>قیمت نهایی</th><th>قیمت</th><th>قیمت در زعفران شاپ</th></tr></thead>\n"

    def process(self, ID, URL, PSelector, DPSelector):
        product = Admin().product(ID)
        C = WebScraper(URL, PSelector, DPSelector)
        return f"<tr><td>{product[0]}</td><td>{C.price}</td><td>{C.discount_price}</td><td>{product[1]}</td></tr>\n"

    def to_html(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_row = {executor.submit(self.process, ID, URL, PSelector, DPSelector): (ID, URL, PSelector, DPSelector) for ID, URL, PSelector, DPSelector in zip(
                self.data["ID"], self.data["URL"], self.data["Price Selector"], self.data["Discount Price Selector"])}

            for future in concurrent.futures.as_completed(future_to_row):
                row = future.result()
                self.html_table += row

        self.html_table += "</table>"

        with open("./app/cache/output.html", "w", encoding="utf-8") as f:
            f.write(self.html_table)


class WebScraper:
    def __init__(self, url, Pselector, DPselector):
        self.soup = self.get_soup(url)
        self.Pselector = Pselector
        self.DPselector = DPselector
        self.price, self.discount_price = self.comparator()

    def init_browser(self):
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--mute-audio")
        options.add_argument("--no-sandbox")
        options.add_argument("--log-level=OFF")
        options.add_argument("--disable-extensions")
        options.add_argument("--window-size=1920x1080")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("disable-infobars")
        service = Service("chromedriver/chromedriver")
        self.browser = webdriver.Chrome(service=service, options=options)

    def get_html(self, url):
        self.init_browser()
        self.browser.get(url)
        html = self.browser.page_source
        return html

    def get_soup(self, url):
        html = self.get_html(url)
        soup = BeautifulSoup(html, 'html.parser')
        return soup

    def letter_eraser(self, money):
        amount = ""
        for char in money:
            if char.isdigit():
                amount += str(char)

        if "۰" or "۱" or "۲" or "۳" or "۴" in money:
            td = {"۰": "0", "۱": "1", "۲": "2", "۳": "3", "۴": "4",
                  "۵": "5", "۶": "6", "۷": "7", "۸": "8", "۹": "9"}
            ed = ""
            for char in amount:
                if char in td:
                    ed += td[char]
                else:
                    ed += char
            amount = ed

        if "ریال" in money:
            amount = amount.replace("0", "", 1)
        return amount

    def comparator(self):

        if self.soup.select_one(self.Pselector):
            price = self.letter_eraser(self.soup.select_one(
                self.Pselector).text.strip())

            if self.soup.select_one(self.DPselector):
                discunt_price = self.letter_eraser(self.soup.select_one(
                    self.DPselector).text.strip())
            else:
                discunt_price = ""

        else:
            price, discunt_price = "ناموجود", ""

        return price, discunt_price


class Admin:
    def __init__(self):
        self.domain = MyShop.select().first().domain
        self.token = MyShop.select().first().token

    def product_update(self, id_product, price):
        url = f"https://{self.domain}/api/products/{id_product}?ws_key={self.token}"

        response = requests.get(url)

        data = xmltodict.parse(response.text)

        data["prestashop"]["product"].pop("manufacturer_name", None)
        data["prestashop"]["product"].pop("quantity", None)
        data["prestashop"]["product"]["price"] = price

        requests.put(url, xmltodict.unparse(data).encode())

    def product(self, id_product):
        url = f"https://{self.domain}/api/products/{id_product}?ws_key={self.token}"

        response = requests.get(url)
        data = xmltodict.parse(response.text)

        name = data["prestashop"]["product"]["name"]["language"]["#text"]
        price = int(float(data["prestashop"]["product"]["price"]))

        return name, price
