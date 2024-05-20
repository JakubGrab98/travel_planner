import streamlit as st
from travel_advice import generate_itinerary

# Title
st.title("Interactive Travel Planning Application")

# Input fields
with st.sidebar:
    destination = st.text_input("Enter your destination:")
    days = st.number_input("Number of days:", min_value=1, max_value=30)
    budget = st.selectbox("Select your budget:", ["Low", "Medium", "High"])
    interests = st.text_input("Enter your interests (e.g., museums, hiking, food):")
    travel_style = st.selectbox("Select your travel style:", ["Relaxed", "Adventurous", "Cultural"])

# Generate conversation button
if st.button("Start Planning"):
    if destination and days and budget and interests and travel_style:
        with st.spinner('Planning your trip...'):
            conversation = generate_itinerary(destination, days, budget, interests, travel_style)
            st.write(conversation)
    else:
        st.error("Please fill in all fields.")
