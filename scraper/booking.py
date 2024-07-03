import os
from types import TracebackType
from selenium import webdriver
from selenium.webdriver.common.by import By
import const as const
from booking_filter import BookingFilter


class Booking(webdriver.Chrome):
    def __init__(self, driver_path, teardown=False):
        self.driver_path = driver_path
        self.teardown = teardown
        os.environ["PATH"] += self.driver_path
        super(Booking, self).__init__()
        self.implicitly_wait(60)
        self.maximize_window()

    def __exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, traceback: TracebackType | None):
        if self.teardown:
            self.quit()

    def open_first_page(self):
        self.get(const.BOOKING_BASE_URL)

    def accept_cookies(self):
        accept_button = self.find_element(
            By.ID, "onetrust-accept-btn-handler"
        )
        accept_button.click()

    def close_login_window(self):
        close_button = self.find_element(
            By.CSS_SELECTOR, "button[aria-label='Dismiss sign-in info.']"
        )
        if close_button:
            close_button.click()

    def change_currency(self, currency_code):
        currency_element = self.find_element(
            By.CSS_SELECTOR, "button[data-testid='header-currency-picker-trigger']"
        )
        currency_element.click()

        currency_code = self.find_element(
            By.XPATH, "//div[text()='PLN']/ancestor::button"
        )
        currency_code.click()

    def change_language(self):
        pass

    def send_city_key(self, city: str):
        city_box = self.find_element(By.CSS_SELECTOR, "input[name='ss']")
        city_box.clear()
        city_box.send_keys(city)

        first_result = self.find_element(
            By.CSS_SELECTOR, "li[id='autocomplete-result-0']"
        )
        first_result.click()

    def choose_trip_dates(self, check_in_date: str, check_out_date: str):
        self.find_element(
            By.CSS_SELECTOR, "button[data-testid='date-display-field-start']"
        ).click()
        self.find_element(
            By.CSS_SELECTOR, f"span[data-date='{check_in_date}']"
        ).click()
        self.find_element(
            By.CSS_SELECTOR, f"span[data-date='{check_out_date}']"
        ).click()

    def click_search_button(self):
        self.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    def apply_filter(self):
        filter = BookingFilter(driver=self)
        filter.breakfast_included()
        filter.private_bathroom()
        filter.excellent_guest_rates()


