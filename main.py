import streamlit as st
from travel_advice import generate_travel_plan
from utils import get_today_date, get_tomorrow_date, get_future_date
from flight_search import FlightSearch


def generate_full_itinerary(flight_details, travel_plan):
    return f"{str(flight_details)}\n{travel_plan}"


if __name__ == "__main__":

    st.title("Interactive Travel Planning Application")

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
        budget = st.selectbox("Select your budget:", ["Low", "Medium", "High"])
        interests = st.text_input("Enter your interests (e.g., museums, hiking, food):")
        travel_style = st.selectbox("Select your travel style:", ["Relaxed", "Adventurous", "Cultural"])

    if st.button("Start Planning"):
        if destination and days and budget and interests and travel_style:
            with st.spinner('Planning your trip...'):
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
                travel_plan = generate_travel_plan(destination, days, budget, interests, travel_style)
                #conversation = generate_full_itinerary(flight_details, travel_plan)
                st.markdown("## Flight Details")
                st.write(f"""
                    **Flight from**: {flight_details.origin_city} ({flight_details.origin_airport}) to: {flight_details.destination_city} ({flight_details.destination_airport}),

                    **Deperture**: {flight_details.departure_date} | {flight_details.departure_time}
                    **Return**: {flight_details.return_date} | {flight_details.return_time}

                    **Price**: {flight_details.price} PLN
                """)
                st.markdown("## Travel Plan")
                st.write(travel_plan)
        else:
            st.error("Please fill in all fields.")
