from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from pydantic import BaseModel, Field
from app.tools.base import BaseTravelTool
from app.core.config import get_settings
from app.core.logging import logger

class CalendarEvent(BaseModel):
    """Model for calendar event data."""
    summary: str = Field(..., description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    start_time: datetime = Field(..., description="Event start time")
    end_time: datetime = Field(..., description="Event end time")
    location: Optional[str] = Field(None, description="Event location")
    attendees: List[str] = Field(default_factory=list, description="Event attendees")

class CalendarTool(BaseTravelTool):
    """Tool for managing Google Calendar events."""
    
    name: str = "calendar"
    description: str = "Create and manage travel events in Google Calendar"
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.description
        )
        self.settings = get_settings()
        self.credentials = None
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google Calendar API."""
        try:
            creds = None
            # Load credentials from token file if it exists
            if self.settings.GOOGLE_CREDENTIALS_FILE.exists():
                creds = Credentials.from_authorized_user_file(
                    str(self.settings.GOOGLE_CREDENTIALS_FILE),
                    self.SCOPES
                )

            # If credentials are invalid or don't exist, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.settings.GOOGLE_CLIENT_SECRETS_FILE),
                        self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)

                # Save credentials for future use
                with open(self.settings.GOOGLE_CREDENTIALS_FILE, 'w') as token:
                    token.write(creds.to_json())

            self.credentials = creds
            self.service = build('calendar', 'v3', credentials=creds)
            logger.info("Successfully authenticated with Google Calendar API")

        except Exception as e:
            logger.error(f"Failed to authenticate with Google Calendar API: {str(e)}")
            raise

    async def _arun(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle calendar operations asynchronously."""
        try:
            if not self.service:
                self._authenticate()

            operation = event_data.get('operation', 'create')
            
            if operation == 'create':
                return await self._create_event(event_data)
            elif operation == 'get':
                return await self._get_event(event_data['event_id'])
            elif operation == 'update':
                return await self._update_event(event_data)
            elif operation == 'delete':
                return await self._delete_event(event_data['event_id'])
            elif operation == 'list':
                return await self._list_events(event_data.get('days', 7))
            else:
                raise ValueError(f"Unknown operation: {operation}")

        except Exception as e:
            return self.handle_error(e)

    async def _create_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new calendar event."""
        event = {
            'summary': event_data['summary'],
            'description': event_data.get('description'),
            'start': {
                'dateTime': event_data['start_time'].isoformat(),
                'timeZone': 'Asia/Seoul',
            },
            'end': {
                'dateTime': event_data['end_time'].isoformat(),
                'timeZone': 'Asia/Seoul',
            },
            'location': event_data.get('location'),
            'attendees': [
                {'email': email}
                for email in event_data.get('attendees', [])
            ],
        }

        event = self.service.events().insert(
            calendarId='primary',
            body=event
        ).execute()

        logger.info(f"Created calendar event: {event['summary']}")
        return self.format_output(event)

    async def _get_event(self, event_id: str) -> Dict[str, Any]:
        """Get a specific calendar event."""
        try:
            event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            return self.format_output(event)
        except Exception as e:
            return self.handle_error(e)

    async def _update_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing calendar event."""
        try:
            event = self.service.events().get(
                calendarId='primary',
                eventId=event_data['event_id']
            ).execute()

            # Update fields
            event['summary'] = event_data.get('summary', event['summary'])
            event['description'] = event_data.get('description', event.get('description'))
            if 'start_time' in event_data:
                event['start'] = {
                    'dateTime': event_data['start_time'].isoformat(),
                    'timeZone': 'Asia/Seoul',
                }
            if 'end_time' in event_data:
                event['end'] = {
                    'dateTime': event_data['end_time'].isoformat(),
                    'timeZone': 'Asia/Seoul',
                }
            event['location'] = event_data.get('location', event.get('location'))
            if 'attendees' in event_data:
                event['attendees'] = [
                    {'email': email}
                    for email in event_data['attendees']
                ]

            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=event_data['event_id'],
                body=event
            ).execute()

            logger.info(f"Updated calendar event: {updated_event['summary']}")
            return self.format_output(updated_event)

        except Exception as e:
            return self.handle_error(e)

    async def _delete_event(self, event_id: str) -> Dict[str, Any]:
        """Delete a calendar event."""
        try:
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            logger.info(f"Deleted calendar event: {event_id}")
            return self.format_output({"status": "success", "message": "Event deleted successfully"})

        except Exception as e:
            return self.handle_error(e)

    async def _list_events(self, days: int = 7) -> Dict[str, Any]:
        """List upcoming calendar events."""
        try:
            now = datetime.now()
            end_time = now + timedelta(days=days)

            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now.isoformat(),
                timeMax=end_time.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            return self.format_output(events)

        except Exception as e:
            return self.handle_error(e)

    async def create_travel_events(self, travel_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Create multiple calendar events from a travel plan."""
        try:
            events = []
            for activity in travel_plan.get('activities', []):
                event_data = {
                    'summary': f"Travel: {activity['name']}",
                    'description': activity.get('description'),
                    'start_time': datetime.fromisoformat(activity['start_time']),
                    'end_time': datetime.fromisoformat(activity['end_time']),
                    'location': activity.get('location'),
                    'operation': 'create'
                }
                
                event = await self._arun(event_data)
                if event['status'] == 'success':
                    events.append(event['data'])

            return self.format_output(events)

        except Exception as e:
            return self.handle_error(e)

    def format_output(self, data: Any) -> Dict[str, Any]:
        """Format the output response."""
        return {
            "status": "success",
            "data": data
        }

    def handle_error(self, error: Exception) -> Dict[str, Any]:
        """Handle errors and format error response."""
        error_message = str(error)
        logger.error(f"Calendar operation failed: {error_message}")
        return {
            "status": "error",
            "error": error_message
        } 