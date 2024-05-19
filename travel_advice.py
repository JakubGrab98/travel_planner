from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

def generate_itinerary(destination, days, budget, interests, travel_style):
    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
    output_parser = StrOutputParser()
    prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful travel assistant."),
            ("user", "I want to plan a trip to {destination} for {days} days."),
            ("assistant", "Sure, I can help with that. What is your budget and interests?"),
            ("user", "My budget is {budget} and I am interested in {interests}."),
        ]
    )

    chain = prompt | llm | output_parser

    res = chain.invoke(
        {
            "destination": destination,
            "days": days,
            "budget": budget,
            "interests": interests,
            "travel_style": travel_style,
        }
    )
    return res
