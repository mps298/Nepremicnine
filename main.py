import asyncio
import time
from aiogram import types, Dispatcher, Bot
from bs4 import BeautifulSoup
from selenium import webdriver
import os

import random


headers = {
    'accept': '*/*',
    'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0'"
}


bot = Bot('TOKEN')
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def start(message: types.message):
    await bot.send_message(message.chat.id, """Zdravo, jaz sem bot ki ti bo pomagal pri iskanju oglasov na spletni 
    strani <b><a href="https://www.nepremicnine.net/">nepremicnine.net</a></b>\nNapiši, kakšne oglase iščeš?""",
                           parse_mode='html',
                           disable_web_page_preview=1)


@dp.message_handler(content_types=['text'])
async def parser(message: types.message):

    # parsing the first page
    message_text = message.text
    url = "https://www.nepremicnine.net/nepremicnine.html?q=" + message_text
    await bot.send_message(message.chat.id,
                           "Prosim, počakajte trenutek, iščem oglase...")

    try:
        options = webdriver.FirefoxOptions()
        options.set_preference("general.useragent.override",
                               "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0")
        driver = webdriver.Firefox(options=options)
        driver.get(url=url)
        time.sleep(random.randint(3, 6))
        with open("response.html", "w", encoding='utf-8') as file:
            file.write(driver.page_source)
        driver.close()
        driver.quit()

    except Exception as exception:
        print(exception)

    with open("response.html", "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file.read(), 'html.parser')

    all_links = soup.find_all("a", class_="url-title-d")

    # parsing next pages in pagination if exist
    page_exists = True
    page_count = 2  # from the 2nd page in pagination
    while page_exists:
        url = f"https://www.nepremicnine.net/oglasi/{page_count}/?q={message_text}"
        try:
            options = webdriver.FirefoxOptions()
            options.set_preference("general.useragent.override",
                                   "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0")
            driver = webdriver.Firefox(options=options)
            driver.get(url=url)
            time.sleep(random.randint(3, 6))
            with open("response.html", "w", encoding='utf-8') as file:
                file.write(driver.page_source)
            driver.close()
            driver.quit()

        except Exception as exception:
            print(exception)

        with open("response.html", "r", encoding="utf-8") as file:
            soup = BeautifulSoup(file.read(), 'html.parser')

        current_page_links = soup.find_all("a", class_="url-title-d")
        if len(current_page_links):
            for link in current_page_links:
                all_links.append(link)
            page_count += 1
        else:
            page_exists = False
            break

    limit = 20
    number = min(len(all_links), limit)
    print(f'number = {number}')

    if number == 0:
        await bot.send_message(message.chat.id, "Ni ustreznih oglasov, poskusite spremeniti parametre iskanja")
    elif number < limit:
        await bot.send_message(message.chat.id, f"Našel sem oglasov: {number}")
    else:
        await bot.send_message(message.chat.id, f"Pošiljam zadnjih {number} zadnjih oglasov:")

    for link in all_links:
        url = link["href"]

        try:
            options = webdriver.FirefoxOptions()
            options.set_preference("general.useragent.override",
                                   "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0")
            driver = webdriver.Firefox(options=options)
            driver.get(url=url)
            time.sleep(random.randint(3, 6))
            with open("response.html", "w", encoding='utf-8') as file:
                file.write(driver.page_source)
            driver.close()
            driver.quit()

        except Exception as exception:
            print(exception)

        with open("response.html", "r", encoding="utf-8") as file:
            soup = BeautifulSoup(file.read(), 'html.parser')

        name = soup.find("h1", class_="podrobnosti-naslov")
        name = name.text

        price = soup.find("div", class_="cena clearfix").find("span").extract()
        price = price.text
        price = price.replace("€", "")
        price = price.replace(" ", "")
        price = price.replace("\n", "")
        price = price.replace(".", "")
        price = price.replace(",", ".")

        image = soup.find("div", class_="rsContainer")
        image = image.findChildren("img")[0]
        image = image["src"]

        await bot.send_photo(message.chat.id, image,
                             caption="<b>" + name + "</b>\n" + price + f"\n<a href='{url}'>Podrobnosti</a>",
                             parse_mode="html")
        if all_links.index(link) == number - 1:
            await bot.send_message(message.chat.id, "To je to")
            break


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
