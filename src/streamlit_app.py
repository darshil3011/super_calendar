import streamlit as st
import re
import json
import os
from openai import OpenAI
from ai_app import openai_function_call
from tools import tools
from tool_executor import ToolExecutor
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

def date_extractor(user_query):
    client = OpenAI(api_key='enter your API KEY here')

    prompt = '''You are a datetime extractor. User will enter a query regarding planning a day. Your task is to just extract
    the date for which the user wants to plan the day.

    For example: "I start my day at 8 AM and work till 5 PM. I need 1 hour lunch break in afternoon.
    On 14th June 2024, I want to schedule a call with my manager but he is only available in mornings and I want to plan a team meeting in afternoon."
    example response: List down all the events for 14th June 2024 from 12 AM to 11:59 PM PST

    Begin !

    User Prompt:  ''' + user_query

    messages = [{"role": "user", "content": prompt}]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
    )

    response_message = response.choices[0].message

    st.write(response_message.content)

    calls = openai_function_call(response_message.content)
    tool_executor = ToolExecutor()
    tool_messages = tool_executor.execute(calls)  # Pass the tool calls to the execute method
    event_list = tool_messages[0]['content']

    return event_list

def planner(user_query, event_list):
    client = OpenAI(api_key='enter your API KEY here')

    prompt = '''You are a calendar planner. I will give you my preferences and you should tell me how should I plan my
    events in pointwise manner. Each point should contain Meeting title, location and date-time.

    Dont change my existing schedule. Only mention plan for new events. Dont mention already planned events.
    Give me my plan of new events in json format as follows.

    {"subtask" : [<subtask 1>, <subtask 2>, <subtask 3>]} followed by justification on why did you plan this way

    Example Prompt:
    I start my day at 8 AM and work till 5 PM. I need 1 hour lunch break in afternoon. My list of events for
    11th june are [{"start": "2024-06-11 12:00 AM", "summary": "Out of office"}, {"start": "2024-06-11 08:00 AM", "summary": "Daily Syncup"}, 
    {"start": "2024-06-11 08:20 AM", "summary": "Jira Updates"}, {"start": "2024-06-11 10:00 AM", "summary": "Call with Meghal"}, {"start": "2024-06-11 08:45 PM", "summary": "Design discussion"}]}
    I want to schedule a call with my manager but he is only available in mornings and I want to plan a team meeting in afternoon.

    Example Response: 
    {"subtask" : ['Create an event for 11th June 2024 9 AM PST with title "Meeting with manager" ', 'Create an event lunch break for 11th June 2024 1 PM - 2 PM', 'Create an event for 11th June 2024 2 PM - 3PM with title 'Team Meeting']}

    As asked, I'd place meeting with manager as early as possible right after Jira updates call. I put up lunch break in afternoon 1-2 and placed
    team meeting call right after that at 2 PM. Thus, your day was planned without making any changes to existing events and withing working hours.

    Begin !

    User Prompt: ''' + user_query + event_list

    messages = [{"role": "user", "content": prompt}]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
    )

    response_message = response.choices[0].message

    copy_response = response_message

    st.write(copy_response.content)

    # Extract the JSON string from the response using regex
    json_match = re.search(r'```json\n(.*?)\n```', response_message.content, re.DOTALL)
    if json_match:
        json_content = json_match.group(1)

        # Parse the JSON string
        parsed_json = json.loads(json_content)

        # Extract the list
        task_list = parsed_json.get("subtask", [])

        # Print the extracted list
        st.write(task_list)
    else:
        st.write("No JSON found in the response")

    for task in task_list:
        calls = openai_function_call(task)
        tool_executor = ToolExecutor()
        tool_messages = tool_executor.execute(calls)  # Pass the tool calls to the execute method
        st.write(tool_messages[0]['content'])

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
                st.error(f"Error refreshing access token: {e}")
                return None
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=8502)
            with open("token.json", "w") as token:
                token.write(creds.to_json())

    return creds

def service_setup(creds):
    service = build("calendar", "v3", credentials=creds)
    return service

def main():
    st.title("Calendar Planner")

    if st.button("Authenticate"):
        creds = auth()
        if creds:
            st.success("Authentication successful!")
        else:
            st.error("Authentication failed. Please try again.")

    user_query = st.text_area('Enter your prompt:')
    
    if st.button("Plan my day"):
        creds = auth()
        if creds is None:
            st.warning("Please authenticate first.")
        else:
            service = service_setup(creds)
            event_list = date_extractor(user_query)
            planner(user_query, str(event_list))

if __name__ == "__main__":
    main()
