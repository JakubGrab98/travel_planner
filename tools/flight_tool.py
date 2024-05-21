from langchain.tools import BaseTool


class FlightTool(BaseTool):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def _run(self, params: dict):
        pass