"""
Tools for interacting with Google Calendar API.
"""
import os
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarTools:
    def __init__(self):
        self.creds = None
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google Calendar API."""
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
        """Create a new calendar event."""
        event = {
            'summary': summary,
            'start': {'dateTime': start_time.isoformat(), 'timeZone': 'America/Toronto'},
            'end': {'dateTime': end_time.isoformat(), 'timeZone': 'America/Toronto'},
        }
        
        if description:
            event['description'] = description
        if location:
            event['location'] = location

        try:
            event = self.service.events().insert(calendarId='primary', body=event).execute()
            return f"Event created successfully: {event.get('htmlLink')}"
        except Exception as e:
            return f"Failed to create event: {str(e)}"

    def list_upcoming_events(self, max_results=10):
        """List upcoming calendar events."""
        now = datetime.utcnow().isoformat() + 'Z'
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
                return "No upcoming events found."
            
            return events
        except Exception as e:
            return f"Failed to retrieve events: {str(e)}"

    def update_event(self, event_id, **updates):
        """Update an existing calendar event."""
        try:
            # First get the event
            event = self.service.events().get(calendarId='primary', eventId=event_id).execute()
            
            # Update the event with new values
            for key, value in updates.items():
                if key in ['start', 'end']:
                    event[key] = {'dateTime': value.isoformat(), 'timeZone': 'America/Toronto'}
                else:
                    event[key] = value

            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event
            ).execute()
            
            return f"Event updated successfully: {updated_event.get('htmlLink')}"
        except Exception as e:
            return f"Failed to update event: {str(e)}"

    def delete_event(self, event_id):
        """Delete a calendar event."""
        try:
            self.service.events().delete(calendarId='primary', eventId=event_id).execute()
            return "Event deleted successfully"
        except Exception as e:
            return f"Failed to delete event: {str(e)}" 