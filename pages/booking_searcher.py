import streamlit as st
from scraper.booking import Booking
from utils import get_today_date


if __name__ == "__main__":

    st.title("Booking searcher")

    with st.sidebar:
        destination = st.text_input("Enter your destination city:")
        currency = st.selectbox("Choose currency: ", options=["PLN", "EUR", "USD"])
        date_from = st.date_input(
            "Arrival date:",
            min_value=get_today_date(),
        )
        date_to = st.date_input(
            "Departure date:",
            min_value=get_today_date(),
        )

    if st.button("Start Searching"):
        if destination and date_from and date_to:

            with st.spinner("Searching your hotels..."):
                try:
                    with Booking("chromedriver.exe") as bot:
                        bot.open_first_page()
                        bot.accept_cookies()
                        bot.close_login_window()
                        bot.change_currency(currency)
                        bot.send_city_key(destination)
                        bot.choose_trip_dates(
                            str(date_from), str(date_to),
                        )
                        bot.click_search_button()
                        bot.apply_filter()
                        bot.refresh()
                        report_results = bot.report_results()
                        
                        for result in report_results[:4]:
                            hotel_name, price, url = result
                            st.subheader(f"[{hotel_name}]({url})")
                            st.write(f"Price: {price}")
                except Exception as e:
                    print(f"There is an error {e}")
        else:
            st.error("Please fill in all fields.")
