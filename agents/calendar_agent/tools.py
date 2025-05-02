"""
Tools for interacting with Google Calendar API.
"""
import os
import re
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import logging
import pytz
from agno.tools import Toolkit

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Current date configuration
CURRENT_YEAR = "2025"
CURRENT_MONTH = "05"  # May

# Set timezone for all calendar operations
TIMEZONE = "America/Argentina/Buenos_Aires"

def ensure_correct_date(date_str):
    """
    Ensures dates are in the correct year (2025) and month (May).
    This handles dates in ISO format strings like "2024-06-17T10:00:00-03:00"
    
    Args:
        date_str (str): Date string to correct
        
    Returns:
        str: Corrected date string
    """
    if not isinstance(date_str, str):
        return date_str
        
    # Pattern to match ISO format date: YYYY-MM-DDThh:mm:ss
    pattern = r'^(\d{4})-(\d{2})-(\d{2})(T.*)$'
    match = re.match(pattern, date_str)
    
    if match:
        year, month, day, remainder = match.groups()
        
        # If the year is 2024, change it to 2025
        if year == "2024":
            logger.info(f"Correcting year from {year} to {CURRENT_YEAR}")
            year = CURRENT_YEAR
            
            # If month is between 01-04 or 06-12, set to May (05)
            if month != CURRENT_MONTH and (int(month) < 5 or int(month) > 5):
                logger.info(f"Correcting month from {month} to {CURRENT_MONTH}")
                month = CURRENT_MONTH
                
        corrected_date = f"{year}-{month}-{day}{remainder}"
        logger.info(f"Date corrected from {date_str} to {corrected_date}")
        return corrected_date
    
    return date_str

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
        self.register(self.get_current_date)
        
        self.creds = None
        self.service = None
        try:
            self._authenticate()
            logger.info("Google Calendar authentication successful")
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")

    def get_current_date(self):
        """
        Returns the current date in 2025.
        This ensures the agent always has access to the correct year and month.
        
        Returns:
        - str: Current date string in ISO format, set to 2025-05-DD
        """
        current_system_time = datetime.now()
        forced_2025_date = datetime(
            year=int(CURRENT_YEAR),  # Force year to be 2025
            month=int(CURRENT_MONTH),  # Force month to be May
            day=current_system_time.day,
            tzinfo=pytz.UTC
        )
        date_str = forced_2025_date.strftime("%Y-%m-%d")
        logger.info(f"Current date requested: returning {date_str}")
        return {
            "date": date_str,
            "year": CURRENT_YEAR,
            "month": CURRENT_MONTH,
            "day": str(current_system_time.day).zfill(2),
            "timezone": TIMEZONE,
            "formatted": forced_2025_date.strftime("%A, %B %d, %Y")
        }

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
        - start_time (str/datetime): When the event starts (can be ISO format string or datetime)
        - end_time (str/datetime): When the event ends (can be ISO format string or datetime)
        - description (str, optional): Detailed description of the event
        - location (str, optional): Where the event takes place
        
        Returns:
        - str: Success message with the event link if successful (format: "Event created successfully: https://calendar.google.com/...")
        - str: Error message if failed (format: "Failed to create event: [error details]")
        """
        logger.info(f"Create event request received with: summary={summary}, start_time={start_time}, end_time={end_time}")
        
        # Handle both string and datetime inputs
        if isinstance(start_time, str):
            # Log the original string for debugging
            logger.info(f"Original start_time (string): {start_time}")
            # Apply date correction for 2025
            start_datetime = ensure_correct_date(start_time)
        else:
            # It's a datetime object, log original object
            logger.info(f"Original start_time (datetime object): year={start_time.year}, month={start_time.month}, day={start_time.day}")
            # Force the year to 2025 directly on the datetime object
            forced_start_time = datetime(
                year=int(CURRENT_YEAR),
                month=start_time.month if start_time.month == int(CURRENT_MONTH) else int(CURRENT_MONTH),
                day=start_time.day,
                hour=start_time.hour,
                minute=start_time.minute,
                second=start_time.second,
                microsecond=start_time.microsecond,
                tzinfo=start_time.tzinfo if start_time.tzinfo else pytz.timezone(TIMEZONE)
            )
            start_datetime = forced_start_time.isoformat()
            
        if isinstance(end_time, str):
            # Log the original string for debugging
            logger.info(f"Original end_time (string): {end_time}")
            # Apply date correction for 2025
            end_datetime = ensure_correct_date(end_time)
        else:
            # It's a datetime object, log original object
            logger.info(f"Original end_time (datetime object): year={end_time.year}, month={end_time.month}, day={end_time.day}")
            # Force the year to 2025 directly on the datetime object
            forced_end_time = datetime(
                year=int(CURRENT_YEAR),
                month=end_time.month if end_time.month == int(CURRENT_MONTH) else int(CURRENT_MONTH),
                day=end_time.day,
                hour=end_time.hour,
                minute=end_time.minute,
                second=end_time.second,
                microsecond=end_time.microsecond,
                tzinfo=end_time.tzinfo if end_time.tzinfo else pytz.timezone(TIMEZONE)
            )
            end_datetime = forced_end_time.isoformat()
            
        # Log the final datetime values for debugging
        logger.info(f"Creating event with CORRECTED datetime values - start: {start_datetime}, end: {end_datetime}")
            
        event = {
            'summary': summary,
            'start': {'dateTime': start_datetime, 'timeZone': TIMEZONE},
            'end': {'dateTime': end_datetime, 'timeZone': TIMEZONE},
        }
        
        if description:
            event['description'] = description
        if location:
            event['location'] = location

        try:
            event = self.service.events().insert(calendarId='primary', body=event).execute()
            link = event.get('htmlLink')
            formatted_link = f"\033]8;;{link}\033\\{link}\033]8;;\033\\"
            logger.info(f"Event created successfully with link: {link}")
            return f"Event created successfully: {formatted_link}"
        except Exception as e:
            logger.error(f"Failed to create event: {str(e)}")
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
            "start": {"dateTime": "2025-05-01T10:00:00-04:00", "timeZone": "America/Argentina/Buenos_Aires"},
            "end": {"dateTime": "2025-05-01T11:00:00-04:00", "timeZone": "America/Argentina/Buenos_Aires"},
            "description": "Event description",
            "location": "Event location",
            "htmlLink": "https://calendar.google.com/..."
            }
        - str: Error message if failed (format: "Failed to retrieve events: [error details]")
        """
        print("List upcoming events...")
        logger.info(f"Attempting to list {max_results} upcoming events")
        
        # Instead of using the system's current time which might be 2024,
        # force the year to be 2025 and use current month/day
        current_system_time = datetime.now()
        forced_2025_time = datetime(
            year=int(CURRENT_YEAR),  # Force year to be 2025
            month=current_system_time.month,
            day=current_system_time.day,
            hour=current_system_time.hour,
            minute=current_system_time.minute,
            second=current_system_time.second,
            microsecond=current_system_time.microsecond,
            tzinfo=pytz.UTC
        )
        now = forced_2025_time.isoformat()
        logger.info(f"Using forced time in 2025: {now}")
        
        try:
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])

            if not events:
                logger.info("No upcoming events found")
                return "No upcoming events found."
            
            # Add clickable links to events
            for event in events:
                if 'htmlLink' in event:
                    link = event['htmlLink']
                    formatted_link = f"\033]8;;{link}\033\\{link}\033]8;;\033\\"
                    event['htmlLink'] = formatted_link
                    # Log the original link for debugging
                    logger.info(f"Event link found: {link}")
            
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
            - start (str/datetime): New start time
            - end (str/datetime): New end time
        
        Returns:
        - str: Success message with the updated event link if successful (format: "Event updated successfully: https://calendar.google.com/...")
        - str: Error message if failed (format: "Failed to update event: [error details]")
        """
        logger.info(f"Update event request received with event_id={event_id}, updates={updates}")
        
        try:
            # First get the event
            event = self.service.events().get(calendarId='primary', eventId=event_id).execute()
            
            # Update the event with new values
            for key, value in updates.items():
                if key in ['start', 'end']:
                    # Handle both string and datetime inputs
                    if isinstance(value, str):
                        # Log the original string for debugging
                        logger.info(f"Original {key} time (string): {value}")
                        # Apply date correction for 2025
                        datetime_str = ensure_correct_date(value)
                    else:
                        # It's a datetime object, log original object
                        logger.info(f"Original {key} time (datetime object): year={value.year}, month={value.month}, day={value.day}")
                        # Force the year to 2025 directly on the datetime object
                        forced_time = datetime(
                            year=int(CURRENT_YEAR),
                            month=value.month if value.month == int(CURRENT_MONTH) else int(CURRENT_MONTH),
                            day=value.day,
                            hour=value.hour,
                            minute=value.minute,
                            second=value.second,
                            microsecond=value.microsecond,
                            tzinfo=value.tzinfo if value.tzinfo else pytz.timezone(TIMEZONE)
                        )
                        datetime_str = forced_time.isoformat()
                    
                    logger.info(f"Setting {key} time to CORRECTED value: {datetime_str}")
                    event[key] = {'dateTime': datetime_str, 'timeZone': TIMEZONE}
                else:
                    event[key] = value

            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event
            ).execute()
            
            link = updated_event.get('htmlLink')
            formatted_link = f"\033]8;;{link}\033\\{link}\033]8;;\033\\"
            logger.info(f"Event updated successfully with link: {link}")
            return f"Event updated successfully: {formatted_link}"
        except Exception as e:
            logger.error(f"Failed to update event: {str(e)}")
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
            self.service.events().delete(calendarId='primary', eventId=event_id).execute()
            return "Event deleted successfully"
        except Exception as e:
            logger.error(f"Failed to delete event: {str(e)}")
            return f"Failed to delete event: {str(e)}" 