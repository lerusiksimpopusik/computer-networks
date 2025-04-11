import csv
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

options = Options()
options.add_argument("--headless")
options.add_argument("--disable-blink-features=AutomationControlled")
service = Service()
driver = webdriver.Chrome(service=service, options=options)
# driver.maximize_window()

base_url = "https://novosibirsk.cian.ru/cat.php?deal_type=rent&engine_version=2&location%5B0%5D=201245&offer_type=flat&p={}&room1=1&room2=1&type=4"

data = []

try:
    for page in range(1, 4):
        print(f"open page {page}")
        driver.get(base_url.format(page))

        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//article[@data-name='CardComponent']"))
        )

        flats = driver.find_elements(By.XPATH, "//article[@data-name='CardComponent']")

        for flat in flats:
            try:
                link = flat.find_element(By.XPATH, ".//a[@href]").get_attribute("href")
                title_elements = flat.find_elements(By.XPATH, ".//span[@data-mark='OfferTitle']")
                subtitle_elements = flat.find_elements(By.XPATH, ".//span[@data-mark='OfferSubtitle']")
                price_element = flat.find_element(By.XPATH, ".//span[@data-mark='MainPrice']")
                address_elements = flat.find_elements(By.XPATH, ".//a[@data-name='GeoLabel']")

                title = (
                    " ".join([elem.text for elem in title_elements]) + " " +
                    " ".join([elem.text for elem in subtitle_elements])
                )
                price = price_element.text
                address = ", ".join([elem.text for elem in address_elements])

                data.append([title.strip(), price.strip(), address.strip(), link])
            except Exception as e:
                print(f"failed to retrieve some items: {e}")

        time.sleep(2)

except Exception as e:
    print(f"error in parsing process: {e}")

finally:
    driver.quit()

with open("flats.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file, delimiter=",")
    writer.writerow(["Название", "Цена", "Адрес", "Ссылка"])
    writer.writerows(data)

print("save in flats.csv")
