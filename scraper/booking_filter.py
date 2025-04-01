from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By


class BookingFilter:
    def __init__(self, driver: WebDriver):
        self.driver = driver

    def breakfast_included(self):
        breakfast_button = self.driver.find_element(
            By.CSS_SELECTOR, 'div[data-filters-item="mealplan:mealplan=1"]'
        )
        breakfast_button.click()

    def private_bathroom(self):
        bathroom_button = self.driver.find_element(
            By.CSS_SELECTOR, "div[data-filters-item='roomfacility:roomfacility=38']"
        )
        bathroom_button.click()

    def excellent_guest_rates(self):
        excellent = self.driver.find_element(
            By.CSS_SELECTOR, "div[data-filters-item='review_score:review_score=90']"
        )
        excellent.click()
        very_good = self.driver.find_element(
            By.CSS_SELECTOR, "div[data-filters-item='review_score:review_score=80']"
        )
        very_good.click()
        
    def sort_results(self):
        dropdown_list = self.driver.find_element(
            By.CSS_SELECTOR, "button[data-testid='sorters-dropdown-trigger']"
        )
        dropdown_list.click()

        cheapiest_price = self.driver.find_element(
            By.CSS_SELECTOR, "button[data-id='review_score_and_price']"
        )
        cheapiest_price.click()
