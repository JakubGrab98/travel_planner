from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv


itinerary_template = """
Create a {days}-day travel itinerary for {destination} considering the following preferences:
- Budget: {budget}
- Interests: {interests}
- Travel style: {travel_style}
"""

load_dotenv()

def generate_travel_plan(destination, days, budget, interests, travel_style):
    llm = ChatOpenAI(temperature=0)
    output_parser = StrOutputParser()
    prompt = PromptTemplate(
        input_variables=["destination", "days", "budget", "interests", "travel_style"],
        template=itinerary_template
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
