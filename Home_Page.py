"""Streamlit page with interface for create user's travel plan."""
import logging
import logging.config
import json
from pathlib import Path
import streamlit as st
from itinerary_tool import generate_travel_plan


logger = logging.getLogger(__name__)

def setup_logging() -> None:
    """Function setups logging confguration using config.json file.
    """
    config_file = Path("logging_configs/config.json")
    try:
        with open(config_file) as file:
            config = json.load(file)
        logging.config.dictConfig(config)
    except FileNotFoundError:
        logging.error("Logging configuration file not found.")
    except json.JSONDecodeError:
        logger.error("Invalid JSON in the logging configuration file.")


if __name__ == "__main__":
    setup_logging()

    st.title("Interactive Travel Planning Application")
    st.sidebar.success("Select a page above")

    with st.sidebar:
        destination = st.text_input("Enter your destination city:")
        days = st.number_input("Number of days:", min_value=1, max_value=30)
        budget = st.selectbox("Select your budget:", ["Low", "Medium", "High"])
        interests = st.text_input("Enter your interests (e.g., museums, hiking, food):")
        travel_style = st.selectbox(
            "Select your travel style:", ["Relaxed", "Adventurous", "Cultural"]
        )

    if st.button("Start Planning"):
        if (
            destination and days and budget 
            and interests and travel_style
        ):
            with st.spinner('Planning your trip...'):
                travel_plan = generate_travel_plan(
                    destination, int(days), budget, interests, travel_style,
                )
                st.markdown("## Travel Plan")
                st.write(travel_plan)
        else:
            st.error("Please fill in all fields.")
