"""
Calendar Agent implementation for KAI.
"""
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from .tools import GoogleCalendarTools

class CalendarAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Calendar Agent",
            model=OpenAIChat("gpt-4o-mini"),
            instructions="""
            You are KAI's Calendar Management Agent, responsible for handling all calendar-related tasks.
            
            CAPABILITIES:
            1. Create new calendar events with:
                - Event title/summary
                - Start and end times
                - Description (optional)
                - Location (optional)
            
            2. List upcoming events
            3. Update existing events
            4. Delete events
            
            RESPONSE FORMAT:
            1. Acknowledge the request
            2. Confirm the action being taken
            3. Provide the result or any error messages
            4. Suggest next steps if applicable
            
            Always maintain a helpful and professional tone while interacting with users.
            """,
            tools=[GoogleCalendarTools()],
            markdown=True
        )

    async def process_calendar_request(self, request):
        """
        Process calendar-related requests and return appropriate responses.
        This method can be called by the main KAI agent when delegating calendar tasks.
        """
        return await self.arun(request) 