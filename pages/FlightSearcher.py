import streamlit as st
from utils import get_today_date, get_tomorrow_date, get_future_date
from flight_search import FlightSearch


if __name__ == "__main__":

    st.title("The Cheapiest Flight Browser")
    st.write("Searching for the chapiest flight based on provided parameters.")
    st.sidebar.success("Select a page above")

    with st.sidebar:
        departure_city = st.text_input("Enter your departure city:")
        destination = st.text_input("Enter your destination city:")
        days = st.number_input("Number of days:", min_value=1, max_value=30)
        date_from = st.date_input(
            "Start date to search flight details:",
            min_value=get_today_date(),
        )
        date_to = st.date_input(
            "End date to search flight details:",
            min_value=get_today_date(),
        )

    if st.button("Start Searching"):
        if destination and days and departure_city and date_from and date_to:
            with st.spinner("Searching your flight..."):
                flight_search = FlightSearch()

                api_params = {
                    "fly_from": flight_search.get_airport_code(str(departure_city)),
                    "fly_to": flight_search.get_airport_code(str(destination)),
                    "one_for_city": 1,
                    "curr": "PLN",
                    "max_stopovers": 1,
                    "nights_in_dst_from": int(days),
                    "nights_in_dst_to": int(days),
                    "date_from": get_tomorrow_date(),
                    "date_to": get_future_date(),
                }
                flight_details = flight_search.get_flight_data(api_params)
                st.markdown("## Flight Details")
                st.write(f"""
                    **Flight from**: {flight_details.origin_city} ({flight_details.origin_airport}) to: {flight_details.destination_city} ({flight_details.destination_airport}),
                    Airlines: {flight_details.airlines}

                    **Deperture**: {flight_details.departure_date} | {flight_details.departure_time}
                    **Return**: {flight_details.return_date} | {flight_details.return_time}

                    **Price**: {flight_details.price} PLN
                """)
        else:
            st.error("Please fill in all fields.")
