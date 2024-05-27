import streamlit as st
from travel_advice import generate_travel_plan


if __name__ == "__main__":

    st.title("Interactive Travel Planning Application")
    st.sidebar.success("Select a page above")

    with st.sidebar:
        destination = st.text_input("Enter your destination city:")
        days = st.number_input("Number of days:", min_value=1, max_value=30)
        budget = st.selectbox("Select your budget:", ["Low", "Medium", "High"])
        interests = st.text_input("Enter your interests (e.g., museums, hiking, food):")
        travel_style = st.selectbox("Select your travel style:", ["Relaxed", "Adventurous", "Cultural"])

    if st.button("Start Planning"):
        if destination and days and budget and interests and travel_style:
            with st.spinner('Planning your trip...'):
                travel_plan = generate_travel_plan(
                    destination, days, budget, interests, travel_style,
                )
                st.markdown("## Travel Plan")
                st.write(travel_plan)
        else:
            st.error("Please fill in all fields.")
