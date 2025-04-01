from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BookingReport:
    def __init__(self, hotel_section_element: WebElement):
        self.hotel_section_element = hotel_section_element
        self.hotel_boxes = self.get_hotel_boxes()
    
    def get_hotel_boxes(self):
        try:
            return WebDriverWait(self.hotel_section_element, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[data-testid='property-card']"))
            )
        except Exception as e:
            print(f"Error finding hotel boxes: {e}")
            return []

    def get_hotel_details(self):
        hotel_details = []
        for hotel_box in self.hotel_boxes:
            try:
                hotel_name = hotel_box.find_element(
                    By.CSS_SELECTOR, "div[data-testid='title']"
                ).get_attribute("innerHTML")

                hotel_price = hotel_box.find_element(
                    By.CSS_SELECTOR, "span[data-testid='price-and-discounted-price']"
                ).get_attribute("innerHTML")

                hotel_link = hotel_box.find_element(
                    By.CSS_SELECTOR, "a[data-testid='title-link']"
                ).get_attribute("href")

                hotel_details.append([hotel_name, hotel_price, hotel_link])
            except Exception as e:
                print(f"Error finding hotel name in box: {e}")
        return hotel_details
