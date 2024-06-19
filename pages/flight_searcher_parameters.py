import streamlit as st
from utils import get_today_date

connection = st.connection("postgresql", "sql", **st.secrets["postgresql"])


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
        if st.button("Create a new parameter"):
            connection.query(f"""INSERT INTO public.search_parameters
                             VALUES (DEFAULT, {departure_city}, {destination}, {days}, {date_from}, {date_to})""")

    elif option=="Read":
        st.subheader("Your parameters")
        select = "SELECT * FROM public.search_parameters;"
        df = connection.query(select, ttl = "10m")

        st.dataframe(df)
    elif option=="Update":
        st.subheader("Update your parameters")
    elif option=="Delete":
        st.subheader("Delete a Record")
