from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

class BookingReport:
    def __init__(self, hotel_section_element: WebElement):
        self.hotel_section_element = hotel_section_element
        self.hotel_boxes = self.get_hotel_boxes()
    
    def get_hotel_boxes(self):
        return self.hotel_section_element.find_element(
            By.CLASS_NAME, "efa3f4d6ac e54292ee17"           
        )

    def get_hotel_name(self):
        for hotel_box in self.hotel_boxes:
            hotel_name = hotel_box.find_element(
                By.CSS_SELECTOR, "div[data-testid='title']"
            ).get_attribute("innerHTML").strip()
            print(hotel_name)
