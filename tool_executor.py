import json
from tools import create_event, get_events

functions = { "create_event": create_event, "get_events": get_events}

class ToolExecutor: 

    def execute(self, calls):
        """Call the specified functions with arguments"""
        tool_messages = []
        if calls:
            for tool_call in calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                function_to_call = functions.get(function_name)
                if function_to_call:
                    function_response = function_to_call(**function_args)
                    response_entry = {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                    tool_messages.append(response_entry)

        return tool_messages