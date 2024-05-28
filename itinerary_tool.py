"""Module responsible for generating responses about travel plan using langchain and OpenAI LLM."""
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv


ITINERARY_TEMPLATE = """
You are a helpful travel assistant.
Create a {days}-day travel itinerary for {destination} considering the following preferences:
- Budget: {budget}
- Interests: {interests}
- Travel style: {travel_style}
"""

load_dotenv()

def generate_travel_plan(
        destination: str, days: int, budget: str, interests: str, travel_style: str
    ) -> str:
    """Generates travel plan based on provided by user parameters.

    Args:
        destination (str): Name of the destination city.
        days (int): Lenght of trip in days.
        budget (str): Type of budget.
        interests (str): User's interests.
        travel_style (str): User's travel style.

    Returns:
        str: Generated response with travel plan.
    """
    llm = ChatOpenAI(temperature=0, model_name="gpt-4-turbo")
    output_parser = StrOutputParser()
    prompt = PromptTemplate(
        input_variables=["destination", "days", "budget", "interests", "travel_style"],
        template=ITINERARY_TEMPLATE
    )

    chain = prompt | llm | output_parser

    response = chain.invoke(
        {
            "destination": destination,
            "days": days,
            "budget": budget,
            "interests": interests,
            "travel_style": travel_style,
        }
    )
    return response
