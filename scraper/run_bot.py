from booking import Booking

with Booking("chromedriver.exe") as bot:
    bot.open_first_page()
    bot.accept_cookies()
    bot.close_login_window()
    bot.change_currency("PLN")
    bot.send_city_key("Barcelona")
    bot.choose_trip_dates("2024-07-01", "2024-07-10")
    bot.click_search_button()
    bot.apply_filter()