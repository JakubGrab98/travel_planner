from langchain.tools import BaseTool
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import PromptTemplate


class ItineraryTool(BaseTool):
    name = "Get Travel Plan"
    description = "Useful when you need to get a the travel plan based on specific parameters."
    
    def __init__(self, llm, itinerary_template):
        self.llm = llm
        self.itinerary_template = itinerary_template

    def _run(self, destination, days, budget, interests, travel_style):
        output_parser = StrOutputParser()
        prompt = PromptTemplate(
            input_variables=["destination", "days", "budget", "interests", "travel_style"],
            template=self.itinerary_template
        )

        chain = prompt | self.llm | output_parser

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
