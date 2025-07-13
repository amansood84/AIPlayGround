# This client has been build through the following reference
# https://github.com/jlowin/fastmcp#mcp-clients

import asyncio
from fastmcp import Client
import pprint
import json
from typing import Dict, Any
from mistralai import Mistral
from mcp.types import Tool
import re
import time
import os
from termcolor import colored, cprint
import io

"""
Initializes the leave management system.
"""
leave_data = {
    1001: {"name": "Alice Smith", "leave_balance": 15, "leaves_taken": ["2025-01-01", "2025-02-14"]},
    1002: {"name": "Bob Johnson", "leave_balance": 10, "leaves_taken": ["2025-01-04"]},
    1003: {"name": "Charlie Brown", "leave_balance": 20, "leaves_taken": ["2025-04-01", "2025-05-05"]},
}

def convert_fastmcp_tool_to_mistral_function(fastmcp_tool: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts a single FastMCP tool dictionary (as returned by client.list_tools())
    to the Mistral Chat Completion API's function tool format.
    """
    # FastMCP's 'parameters' field is already a JSON Schema object
    # We just need to ensure it's structured correctly for Mistral.

    # Mistral's 'parameters' should always have 'type: object' at the top level
    # FastMCP's `parameters` is usually already structured this way for tool arguments.

    mistral_parameters = fastmcp_tool.get("parameters", {"type": "object", "properties": {}, "required": []})

    # Ensure 'type' is "object" at the root of parameters
    if "type" not in mistral_parameters:
        mistral_parameters["type"] = "object"
    if "properties" not in mistral_parameters:
        mistral_parameters["properties"] = {}
    if "required" not in mistral_parameters:
        mistral_parameters["required"] = []

    # FastMCP's schema generation from type hints and docstrings is quite good,
    # so the 'properties' and 'required' fields should largely align.
    # We just need to extract and format.

    return {
        "type": "function",
        "function": {
            "name": fastmcp_tool["name"],
            "description": fastmcp_tool.get("description", ""),
            "parameters": mistral_parameters
        }
    }

def generate_llm_response(msg: str, tools: str) -> str:
    """
    Function to call LLM for interaction

    Args:
        prompt: The prompt to send to the LLM.

    Returns:
        The LLM's response as a string.
    """
    cprint(f"\nDebug: Sending prompts to LLM:", (252, 3, 107))
    index = 0
    for m in msg:
        index = index + 1
        cprint(f"\nDebug: Prompt({index}): {m}", (252, 3, 107))
    API_KEY = os.getenv("M_API_KEY")
    MODEL = "mistral-large-latest"

    client = Mistral(api_key=API_KEY)

    chat_response = client.chat.complete(
        model = MODEL,
        messages = msg,
        tools = tools,
        tool_choice = "auto"
    )

    cprint (f"\nDebug: Received response from LLM: {chat_response}", (252, 3, 107))
    return chat_response

async def main():

    cprint (f"\nStarting leave management chat agent", (252, 3, 107))
    async with Client("http://10.146.77.121:80/mcp/") as client:
        fastmcp_tools = await client.list_tools()
        fastmcp_resources = await client.list_resources()
        fastmcp_resource_templates = await client.list_resource_templates()

    cprint (f"\nDebug: Agent Successfully Received Tools from MCP Server:", (252, 3, 107))
    for tool in fastmcp_tools:
        # Create an in-memory text buffer
        buffer = io.StringIO()
        pprint.pprint (json.dumps(str(tool)), stream=buffer)
        # Get the pretty-printed string from the buffer
        pretty_string = buffer.getvalue()

        # Print the colored string using cprint
        cprint(f"{pretty_string}", (252, 3, 107))

    cprint (f"\nDebug: Agent Successfully Received Resource from MCP Server:", (252, 3, 107))
    for resource in fastmcp_resources:
        # Create an in-memory text buffer
        buffer = io.StringIO()
        pprint.pprint (json.dumps(str(resource)), stream=buffer)
        # Get the pretty-printed string from the buffer
        pretty_string = buffer.getvalue()

        # Print the colored string using cprint
        cprint(f"{pretty_string}", (252, 3, 107))

    cprint (f"\nDebug: Agent Successfully Received Resource Templates from MCP Server:", (252, 3, 107))
    for resource_t in fastmcp_resource_templates:
        # Create an in-memory text buffer
        buffer = io.StringIO()
        pprint.pprint (json.dumps(str(resource_t)), stream=buffer)
        # Get the pretty-printed string from the buffer
        pretty_string = buffer.getvalue()

        # Print the colored string using cprint
        cprint(f"{pretty_string}", (252, 3, 107))

    # Convert the tools received from MCP to the function format expected by Mistral 
    mistral_tools = []
    for tool_data in fastmcp_tools:
        mistral_tools.append(convert_fastmcp_tool_to_mistral_function(tool_data.model_dump()))

#    curr_user_id = None
    message = []

    # Fetch the system prompt
    # I should actually be fetching the prompt from the resource that MCP sent instead
    # of using the hardcoded string here
    system_uri = f"resource://get_system_prompt"
    async with Client("http://10.146.77.121:80/mcp/") as client:
        system_prompt_str = await client.read_resource(system_uri)
        system_prompt = json.loads(system_prompt_str[0].text)
        system_prompt_content = system_prompt["content"]
        cprint (f"\nDebug: Fetching system prompt from MCP Resource: {system_prompt_content}", (252, 3, 107))

    system_msg = {    
                    "role" : "system",
                    "content": json.dumps(system_prompt_content),
                 }
    message.append(system_msg)

    cprint("\n ** Welcome! I am a Leave management agent. Type 'quit' to stop. **", (252, 3, 107))


    while True:
        # Ask user for its input prompt
        user_input = input("You: ")
        if user_input.lower() == "quit":
            cprint(f"Agent: Goodbye!",(3, 219, 252))
            break

        # System prompt is the 1st in the message list.
        # Reset chat history after every 10 conversations
        # I am assuming that the employee id will follow the keyword employee or and its a 4 digit number 
        if (len(message) >=11):
            del message[1:]
            cprint (f"\nDebug: Clearing Message Cache", (252, 3, 107))
#        match = re.search("employee.*(\d{4})", user_input, flags=re.IGNORECASE)
#        if (match != None):
#            user_id = match.group(1)
#            if (curr_user_id == None):
#                curr_user_id = user_id
#            elif (curr_user_id != user_id):
#                del message[1:]
#                print (f"\nDebug: Clearing Message Cache")
#            elif (len(message) >=11):
#                del message[1:]
#                print (f"\nDebug: Clearing Message Cache")

    
        user_msg = {
                       "role": "user",
                       "content": user_input,
                   }

        message.append(user_msg)
        response = generate_llm_response(message, mistral_tools)
        

        # If LLM didnt return any tools, print the response and restart the loop
        if (response.choices[0].message.tool_calls == None):
            cprint (f"Debug: LLM doesnt need a tool call", (252, 3, 107))
            cprint (f"Agent: {response.choices[0].message.content}", (3, 219, 252))
            # Add LLM response to chat history
            message.append({"role": "assistant", "content":response.choices[0].message.content})
            continue

        # Parse tool and the parameters from LLM response
        tool_call = response.choices[0].message.tool_calls[0]
        function_name = tool_call.function.name
        function_params = json.loads(tool_call.function.arguments)
        cprint (f"\nDebug: LLM responded with a function call: {function_name}({function_params})", (252, 3, 107))

        # Append the received response to the message
        message.append(response.choices[0].message)

        # Call the tools and resources
        async with Client("http://10.146.77.121:80/mcp/") as client:
            # The function_params are returned as JSON and tool expects JSON
            # When i sent employee id here, it threw an error
            tool_response = await client.call_tool(function_name, function_params)
            cprint (f"\nDebug: Received response from MCP Tool: {tool_response}", (252, 3, 107))

            # Craft the new prompt to llm    
            # ToDo, calling generate_llm_response breaks this.
            # Not sure why, need to check and fix.
            message.append({
                "role":"tool",
                "name":function_name,
                "content":tool_response[0].text,
                "tool_call_id":tool_call.id
            })

#            print(f"\nDebug: Sending prompt to LLM: {message}")
#            MODEL = "mistral-large-latest"

#            client = Mistral(api_key=API_KEY)

#            chat_response = client.chat.complete(
#                model = MODEL,
#                messages = message
#            )

            chat_response = generate_llm_response(message, None)

#            print (f"\nDebug: Received response from LLM: {chat_response}")
            cprint (f"Agent: {chat_response.choices[0].message.content}", (3, 219, 252))
            message.append({"role": "assistant", "content":chat_response.choices[0].message.content})
#            print(f"*****Debug Dumping chat history****")
#            for chat in message:
#                print (f"Debug: Chat History: {chat}")


asyncio.run(main())
