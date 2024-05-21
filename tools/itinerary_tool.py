from typing import Optional, Dict, Any
from langchain.tools import BaseTool
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import PromptTemplate
from langchain.callbacks.manager import CallbackManagerForToolRun

class ItineraryTool(BaseTool):
    name = "Get Travel Plan"
    description = "Useful for generating a travel plan based on specific parameters."

    def __init__(self, llm, itinerary_template: str):
        """
        Initialize the ItineraryTool with an LLM and a prompt template.
        
        :param llm: The language model to use for generating the itinerary.
        :param itinerary_template: The template string for the itinerary prompt.
        """
        self.llm = llm
        self.itinerary_template = itinerary_template

    def run(
        self, input_variables: Dict[str, Any], run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        Generate a travel plan based on input variables.

        :param input_variables: A dictionary of input variables for the prompt.
        :param run_manager: Optional callback manager for managing the tool run.
        :return: A string representing the generated travel plan.
        """
        output_parser = StrOutputParser()
        prompt = PromptTemplate(
            input_variables=list(input_variables.keys()),
            template=self.itinerary_template
        )

        # Combine prompt, llm, and output_parser into a chain
        chain = prompt | self.llm | output_parser

        try:
            response = chain.invoke(input_variables)
        except Exception as e:
            # Handle and log the exception
            if run_manager:
                run_manager.on_tool_error(e)
            return f"An error occurred while generating the travel plan: {e}"

        if run_manager:
            run_manager.on_tool_end(response)
        
        return response
