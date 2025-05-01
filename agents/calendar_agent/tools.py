"""
Tools for interacting with Google Calendar API.
"""
import os
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import logging
from agno.tools import Toolkit

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarTools(Toolkit):
    """
    Tools for interacting with Google Calendar API.
    
    This tool provides calendar management capabilities including creating, listing,
    updating, and deleting events.
    """

    def __init__(self):
        super().__init__(name="google_calendar_tools")
        # Registrar las funciones que serán herramientas para el agente
        self.register(self.create_event)
        self.register(self.list_upcoming_events)
        self.register(self.update_event)
        self.register(self.delete_event)
        
        self.creds = None
        self.service = None
        try:
            self._authenticate()
            logger.info("Google Calendar authentication successful")
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")

    def _authenticate(self):
        """Authenticate with Google Calendar API."""
        logger.info("Starting Google Calendar authentication")
        
        # Check if credentials.json existscrea
        if not os.path.exists('credentials.json'):
            logger.error("credentials.json not found")
            raise FileNotFoundError("credentials.json not found")
        
        # The file token.pickle stores the user's access and refresh tokens
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)

        self.service = build('calendar', 'v3', credentials=self.creds)

    def create_event(self, summary, start_time, end_time, description=None, location=None):
        """
        Creates a new event in the user's Google Calendar.
        
        Parameters:
        - summary (str): The title/summary of the event
        - start_time (datetime): When the event starts
        - end_time (datetime): When the event ends
        - description (str, optional): Detailed description of the event
        - location (str, optional): Where the event takes place
        
        Returns:
        - str: Success message with the event link if successful (format: "Event created successfully: https://calendar.google.com/...")
        - str: Error message if failed (format: "Failed to create event: [error details]")
        """
        event = {
            'summary': summary,
            'start': {'dateTime': start_time.format(), 'timeZone': 'America/Toronto'},
            'end': {'dateTime': end_time.format(), 'timeZone': 'America/Toronto'},
        }
        
        if description:
            event['description'] = description
        if location:
            event['location'] = location

        try:
            event = self.service.events().insert(calendarId='joaquinlucascortez@gmail.com', body=event).execute()
            return f"Event created successfully: {event.get('htmlLink')}"
        except Exception as e:
            return f"Failed to create event: {str(e)}"

    def list_upcoming_events(self, max_results=10):
        """
        Retrieves a list of upcoming calendar events.
        
        Parameters:
        - max_results (int, optional): Maximum number of events to return (default: 10)
        
        Returns:
        - str: "No upcoming events found." if no events exist
        - list: List of event dictionaries if successful, each containing:
            {
            "id": "event_id_string",
            "summary": "Event title",
            "start": {"dateTime": "2025-05-01T10:00:00-04:00", "timeZone": "America/Toronto"},
            "end": {"dateTime": "2025-05-01T11:00:00-04:00", "timeZone": "America/Toronto"},
            "description": "Event description",
            "location": "Event location",
            "htmlLink": "https://calendar.google.com/..."
            }
        - str: Error message if failed (format: "Failed to retrieve events: [error details]")
        """
        print("List upcoming events...")
        logger.info(f"Attempting to list {max_results} upcoming events")
        now = datetime.utcnow().isoformat() + 'Z'
        try:
            events_result = self.service.events().list(
                calendarId='joaquinlucascortez@gmail.com',
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])

            if not events:
                return "No upcoming events found."
            
            logger.info(f"API call successful, found {len(events)} events")
            return events
        except Exception as e:
            logger.error(f"Failed to retrieve events: {str(e)}")
            return f"Failed to retrieve events: {str(e)}"

    def update_event(self, event_id, **updates):
        """
        Updates an existing calendar event.
        
        Parameters:
        - event_id (str): The ID of the event to update
        - **updates: Keyword arguments for fields to update, which may include:
            - summary (str): New title
            - description (str): New description
            - location (str): New location
            - start (datetime): New start time
            - end (datetime): New end time
        
        Returns:
        - str: Success message with the updated event link if successful (format: "Event updated successfully: https://calendar.google.com/...")
        - str: Error message if failed (format: "Failed to update event: [error details]")
        """
        try:
            # First get the event
            event = self.service.events().get(calendarId='joaquinlucascortez@gmail.com', eventId=event_id).execute()
            
            # Update the event with new values
            for key, value in updates.items():
                if key in ['start', 'end']:
                    event[key] = {'dateTime': value.isoformat(), 'timeZone': 'America/Toronto'}
                else:
                    event[key] = value

            updated_event = self.service.events().update(
                calendarId='joaquinlucascortez@gmail.com',
                eventId=event_id,
                body=event
            ).execute()
            
            return f"Event updated successfully: {updated_event.get('htmlLink')}"
        except Exception as e:
            return f"Failed to update event: {str(e)}"

    def delete_event(self, event_id):
        """
        Deletes a calendar event.
        
        Parameters:
        - event_id (str): The ID of the event to delete
        
        Returns:
        - str: "Event deleted successfully" if successful
        - str: Error message if failed (format: "Failed to delete event: [error details]")
        """
        try:
            self.service.events().delete(calendarId='joaquinlucascortez@gmail.com', eventId=event_id).execute()
            return "Event deleted successfully"
        except Exception as e:
            return f"Failed to delete event: {str(e)}" 