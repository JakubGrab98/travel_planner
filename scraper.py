import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import datetime


service = Service(executable_path="chromedriver.exe")
driver = webdriver.Chrome(service=service)


driver.get("https://www.booking.com/index.pl.html?label=gen173nr-1BCAEoggI46AdIM1gEaLYBiAEBmAEeuAEXyAEM2AEB6AEBiAIBqAIDuALw5eazBsACAdICJDdiMWIwZTJiLTFlZDQtNDRjYy1iNmIzLTYzMTRjN2ZkN2FmMdgCBeACAQ&sid=a9e8ab00d55740fdb75c45479b4f849b&aid=304142")


city = "Warsaw"
date_from = datetime.datetime(2024, 7, 1)
date_to = datetime.datetime(2024, 7, 10)

def date_format(date, format):
    return date.sttftime(format)

try:
    # Wait for the page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, ":re:"))
    )

    # Find the search box element
    search_box = driver.find_element(By.ID, ":re:")
    search_box.send_keys("Warsaw")

    # Open the date picker for check-in
    datefrom_button = driver.find_element(By.CSS_SELECTOR, "button[data-testid='date-display-field-start']")
    datefrom_button.click()

    # Example: Select 1st July 2024 as check-in date
    checkin_date = driver.find_element(By.CSS_SELECTOR, "span[data-date='2024-07-01']")
    checkin_date.click()

    # Example: Select 10th July 2024 as check-out date
    checkout_date_input = driver.find_element(By.CSS_SELECTOR, "span[data-date='2024-07-10']")
    checkout_date_input.click()

    # Find and click the search button
    search_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    search_button.click()

    # Wait for search results to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "sr_property_block"))
    )

    # Extract hotel names
    hotels = driver.find_elements(By.CLASS_NAME, "sr_property_block_main_row")
    for hotel in hotels:
        hotel_name = hotel.find_element(By.CLASS_NAME, "sr-hotel__name").text
        print(hotel_name)

finally:
    # Close the WebDriver after some time
    time.sleep(10)
    driver.quit()
