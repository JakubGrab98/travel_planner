import streamlit as st
from utils import get_today_date, get_tomorrow_date, get_future_date
from flight_search import FlightSearch


if __name__ == "__main__":

    st.title("The Cheapiest Flight Browser")
    st.write("Searching for the chapiest flight based on provided parameters.")
    st.sidebar.success("Select a page above")

    option = st.sidebar.selectbox("Select an Operation", ("Create", "Read", "Update", "Delete"))

    if option=="Create":
        st.subheader("Create a new search parameter")
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
    elif option=="Read":
        st.subheader("Your parameters")
    elif option=="Update":
        st.subheader("Update your parameters")
    elif option=="Delete":
        st.subheader("Delete a Record")
