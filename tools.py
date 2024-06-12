import requests
import json
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os

tools = [ {
            "type": "function",
            "function": {
                "name": "get_events",
                "description": "View upcoming Google calendar events",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "no_of_events": { "type": "string", "description": "Number of upcoming events for eg. 5 means next 5 events", },
                        "start_time": { "type": "string", "description": "Lower bound of the time frame between which you want to list events for, strictly in date time ISO-8601 date time format  (24 Hours format) in PST timezone so add -07:00 for eg. 18th June 2024 9 AM means 2024-06-18T09:00:00-07:00 ", },
                        "end_time": {"type": "string", "description": "Upper bound of the time frame between which you want to list events for, strictly in date time ISO-8601 date time format (24 Hours format) in PST timezone so add -07:00 for eg. 18th June 2024 10 AM means 2024-06-18T10:00:00-07:00 ", },                   
                    },
                    "required": ["no_of_events"],
                },
            },
        },

        {
            "type": "function",
            "function": {
                "name": "create_event",
                "description": "Create an event in Google calendar based on given information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": { "type": "string", "description": "Name of the event eg. Team meeting or Family dinner", },
                        "location": { "type": "string", "description": "Location / Address of the event for eg. 431 El Camino Real, CA", },
                        "start_time": { "type": "string", "description": "Start time of the event, strictly in date time ISO format for eg. 18th June 2024 9 AM means 2024-06-18T09:00:00-07:00 " , },
                        "end_time": { "type": "string", "description": "End time of the event, strictly in date time ISO format for eg. 18th June 2024 10 AM means 2024-06-18T10:00:00-07:00 " , },
                    },
                    "required": ["name", "location", "start_time", "end_time"],
                },
            },
        }

        ]

def get_current_weather(location):
    
    data = {'current':{'temp': '25 degree C', 'wind': '5kmph', 'rain': 'No'}}
    current_weather = data['current']
    print(current_weather)

    return json.dumps(current_weather)

    
def auth():

    creds = None
    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing access token: {e}")
                return
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return creds


def service_setup(creds):
    service = build("calendar", "v3", credentials=creds)
    return service

def get_events(no_of_events, start_time, end_time):

    no_of_events = int(no_of_events)
    creds = auth()
    service = service_setup(creds)

    now = datetime.datetime.utcnow().isoformat() + "Z"

    events_result = service.events().list(
        calendarId="primary",
        timeMin=str(start_time),
        timeMax=str(end_time),
        maxResults=no_of_events,
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    events = events_result.get("items", [])

    if not events:
        return "No upcoming operation found."
    
    event_list = []
    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        # Parse the dateTime string to a datetime object
        start_datetime = datetime.datetime.fromisoformat(start)
        # Format the datetime object to a 12-hour format with AM/PM
        formatted_start = start_datetime.strftime("%Y-%m-%d %I:%M %p")

        event_list.append({"start": formatted_start, "summary": event["summary"]})

    return 'Answer from get_events API : List of existing calendar events between the specified date and time is ' + json.dumps(event_list) + 'Based on this response, Analyse and respond with next task if necessary. Make sure you dont overlap events. If done, reply that task completed.'
    #return json.dumps({'hello':'world'})


def create_event(name, location, start_time, end_time):

    creds = auth()
    service = service_setup(creds)

    event_dict = {
        'summary': name,
        'location': location,
        'description': 'Test meeting created by super calendar',
        'start': { 'dateTime': str(start_time), 'timeZone': 'America/Los_Angeles'},
        'end': {'dateTime': str(end_time), 'timeZone': 'America/Los_Angeles'},
        #'start': {'dateTime': '2024-06-10T09:00:00-07:00', 'timeZone': 'America/Los_Angeles'},
        #'end': {'dateTime': '2024-06-10T17:00:00-07:00', 'timeZone': 'America/Los_Angeles'},
        'attendees': [],
        'reminders': {
            'useDefault': False,
            'overrides': [{'method': 'email', 'minutes': 24 * 60}, {'method': 'popup', 'minutes': 10}]
        }
    }

    created_event = service.events().insert(calendarId='primary', body=event_dict).execute()

    return json.dumps({'Event created' : str(name)})

      