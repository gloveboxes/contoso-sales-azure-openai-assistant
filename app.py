import asyncio
import json
import os
from typing import Any, Callable, Dict
from pathlib import Path

import chainlit as cl
from chainlit.config import config
from chainlit.types import ThreadDict
from openai import AsyncAzureOpenAI, AzureOpenAI, BadRequestError
from dotenv import load_dotenv
import httpx
import openai

from event_handler import EventHandler
from sales_data import SalesData

load_dotenv()

AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY = os.environ.get("AZURE_OPENAI_KEY")
AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION")
OPENAI_ASSISTANT_ID = os.environ.get("OPENAI_ASSISTANT_ID")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_ASSISTANT_ID = os.getenv("AZURE_OPENAI_ASSISTANT_ID")

assistant = None
sales_data = SalesData()
cl.instrument_openai()

function_map: Dict[str, Callable[[Any], str]] = {
    "ask_database": lambda args: sales_data.ask_database(query=args.get("query")),
}


def get_openai_client():
    metadata = cl.user_session.get("user").metadata
    api_key = metadata.get("api_key")

    return AsyncAzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=api_key,
        api_version=AZURE_OPENAI_API_VERSION,
    )


async def authenticate_api_key(api_key: str):
    url = f"{AZURE_OPENAI_ENDPOINT}/eventinfo"
    headers = {"api-key": api_key}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers)
    if response.status_code == 200:
        return response.text
    return None


@cl.password_auth_callback
async def auth_callback(username: str, password: str):
    event_response = await authenticate_api_key(password)
    if event_response:
        event_settings = json.loads(event_response)
        event_settings.update({"api_key": password})
        return cl.User(identifier=username, metadata=event_settings)
    return None


async def initialize(sales_data: SalesData, api_key: str):
    await sales_data.connect()
    database_schema_string = await sales_data.get_database_info()

    instructions = (
        "You are a Contoso sales analysis assistant. Assist users with their sales data inquiries in a polite, professional manner, providing brief explanations.",
        "Access sales data using the `ask_database` function, which returns results in JSON format.",
        "When querying with the ask_database function, default to aggregated data unless a detailed breakdown is requested.",
        f"The sales database follows this SQLite schema: {database_schema_string}.",
        "You can also use the `file_search` tool to retrieve relevant product information.",
        "If a user requests 'help,' provide example questions related to sales data inquiries that you can assist with.",
        "If a query falls outside of sales or your expertise, respond with: 'I'm unable to assist with that. Please contact IT for further help.'",
        "Remain calm and professional if faced with aggressive behavior. Reply with: 'I'm here to help with sales data inquiries. For other issues, please contact IT.'",
        "You have access to a sandboxed environment for writing and testing code.",
        "Present data in markdown tables unless the user specifically requests visualizations.",
        "Ensure that all responses and visualizations match the language used in the user's query.",
        "Do not include markdown links to visualizations in your responses under any circumstances.",
        "For download requests, respond with: 'The download link is provided below.'",
        "For visualizations, follow these steps:",
        "1. Write the necessary code.",
        "2. Run the code to ensure it works.",
        "3. Display the visualization if successful.",
        "4. If an error occurs, show the error, revise the code, and try again.",
    )

    tools_list = [
        {"type": "code_interpreter"},
        {"type": "file_search"},
        {
            "type": "function",
            "function": {
                "name": "ask_database",
                "description": "Use this function to answer user questions about contoso sales data. Input should be a fully formed SQLite query.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": f"""
                                    SQLite query extracting info to answer the user's question.
                                    SQLite should be written using this database schema:
                                    {database_schema_string}
                                    The query should be returned in plain text, not in JSON.
                                    """,
                        }
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
            },
        },
    ]

    try:
        sync_openai_client = AzureOpenAI(
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=api_key,
            api_version=AZURE_OPENAI_API_VERSION,
        )

        assistant = sync_openai_client.beta.assistants.retrieve(assistant_id=AZURE_OPENAI_ASSISTANT_ID)

        sync_openai_client.beta.assistants.update(
            assistant_id=assistant.id,
            name="Portfolio Management Assistant",
            model=AZURE_OPENAI_DEPLOYMENT,
            instructions=str(instructions),
            tools=tools_list,
        )

        config.ui.name = assistant.name
        return assistant
    except openai.NotFoundError as e:
        print(e)
        return None
    except Exception as e:
        print(e)
        return None


@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Help",
            message="help.",
            icon="/public/idea.svg",
        ),
        cl.Starter(
            label="Create a chart of monthly revenue for winter sports products in 2022 in Europe, using vibrant colors.",
            message="Create a chart of monthly revenue for winter sports products in 2022 in Europe, using vibrant colors.",
            icon="/public/learn.svg",
        ),
        cl.Starter(
            label="Staafdiagram van maandelijkse inkomsten voor wintersportproducten in 2023 met levendige kleuren.",
            message="Staafdiagram van maandelijkse inkomsten voor wintersportproducten in 2023 met levendige kleuren.",
            icon="/public/terminal.svg",
        ),
        cl.Starter(
            label="Download excel file for sales by category",
            message="Download excel file for sales by category",
            icon="/public/write.svg",
        ),
    ]


@cl.on_chat_start
async def start_chat():
    global assistant
    try:
        metadata = cl.user_session.get("user").metadata
        api_key = metadata.get("api_key")

        if assistant is None:
            assistant = await initialize(sales_data=sales_data, api_key=api_key)

        async_openai_client = get_openai_client()
        thread_id = cl.user_session.get("thread_id")
        if not thread_id:
            thread = await async_openai_client.beta.threads.create()
            cl.user_session.set("thread_id", thread.id)

    except Exception as e:
        cl.user_session.set("thread_id", None)
        await cl.Message(content=e.response.reason_phrase).send()
        return


@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    await start_chat()


@cl.on_stop
async def stop_chat():
    current_run = cl.user_session.get("current_run")
    if current_run:
        try:
            thread_id = getattr(current_run, "thread_id", None)
            run_id = getattr(current_run, "run_id", None)
            status = getattr(current_run, "status", None)
            async_openai_client = get_openai_client()
            if thread_id and run_id and async_openai_client and status != "completed":
                await async_openai_client.beta.threads.runs.cancel(run_id=run_id, thread_id=thread_id)
                await cl.Message(content=f"Run cancelled. {run_id}").send()
        except Exception:
            pass
        finally:
            cl.user_session.set("current_run", None)


async def get_attachments(message: cl.Message, async_openai_client: AsyncAzureOpenAI) -> Dict:
    file_paths = [file.path for file in message.elements]
    if not file_paths:
        return None

    await cl.Message(content="Uploading files.").send()
    message_files = []
    
    for path in file_paths:
        with Path(path).open("rb") as file:
            uploaded_file = await async_openai_client.files.create(file=file, purpose="assistants")
            message_files.append({"file_id": uploaded_file.id, "tools": [{"type": "file_search"}]})

    await cl.Message(content="Uploading completed.").send()
    return message_files


@cl.on_message
async def main(message: cl.Message) -> None:
    thread_id = cl.user_session.get("thread_id")
    async_openai_client = get_openai_client()

    if not thread_id or not async_openai_client:
        await cl.Message(content="An error occurred. Please try again later.").send()
        return

    message_files = await get_attachments(message, async_openai_client)

    try:
        # Add a Message to the Thread
        await async_openai_client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message.content,
            attachments=message_files,
        )

        # Create and Stream a Run
        async with async_openai_client.beta.threads.runs.stream(
            thread_id=thread_id,
            assistant_id=assistant.id,
            event_handler=EventHandler(
                function_map=function_map,
                assistant_name=assistant.name,
                async_openai_client=async_openai_client,
            ),
            temperature=0.3,
        ) as stream:
            await stream.until_done()

    # triggered when the user stops a chat
    except asyncio.exceptions.CancelledError:
        if stream and stream.current_run and stream.current_run.status != "completed":
            await async_openai_client.beta.threads.runs.cancel(
                run_id=stream.current_run.id, thread_id=stream.current_run.thread_id
            )
            await cl.Message(content=f"Run cancelled. {stream.current_run.id}").send()

    except BadRequestError as e:
        print(e)

    except Exception as e:
        await cl.Message(content=f"An error occurred: {e}").send()
        await cl.Message(content="Please try again in a moment.").send()
