import asyncio
import json
import os
from contextlib import suppress
from pathlib import Path
from typing import Any, Callable, Dict

import chainlit as cl
import httpx
import openai
from chainlit.config import config
from chainlit.types import ThreadDict
from dotenv import load_dotenv
from openai import AsyncAzureOpenAI, AzureOpenAI

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

    instructions = {
        "You are a polite, professional assistant specializing in Contoso sales data analysis. Provide clear, concise explanations.",
        "Use the `ask_database` function for sales data queries, defaulting to aggregated data unless a detailed breakdown is requested. The function returns JSON data.",
        f"Reference the following SQLite schema for the sales database: {database_schema_string}.",
        "Use the `file_search` tool to retrieve product information from uploaded files when relevant. Prioritize Contoso sales database data over files when responding.",
        "For sales data inquiries, present results in markdown tables by default unless the user requests visualizations.",
        "For visualizations: 1. Write and test code in your sandboxed environment. 2. Display successful visualizations or retry upon error.",
        "If asked for 'help,' suggest example queries (e.g., 'What was last quarter's revenue?' or 'Top-selling products in Europe?').",
        "Only use data from the Contoso sales database or uploaded files when responding.",
        "If a query is outside your expertise or unrelated to sales data, respond with: 'I'm unable to assist with that. Please contact IT for further help.'",
        "If faced with aggressive behavior, calmly reply: 'I'm here to help with sales data inquiries. For other issues, please contact IT.'",
        "Tailor responses to the user’s language preferences, including terminology, measurement units, currency, and formats.",
        "For download requests, respond with: 'The download link is provided below.'",
        "Do not include markdown links to visualizations in your responses."
    }

    tools_list = [
        {"type": "code_interpreter"},
        {"type": "file_search"},
        {
            "type": "function",
            "function": {
                "name": "ask_database",
                "description": "This function is used to answer user questions about Contoso sales data by executing SQLite queries against the database.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": f"""
                                The input should be a well-formed SQLite query to extract information based on the user's question. 
                                The query result will be returned as plain text, not in JSON format.
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
            label="Create a vivid pie chart of sales by region.",
            message="Create a vivid pie chart of sales by region.",
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


async def cancel_thread_run(thread_id: str) -> None:
    client = get_openai_client()
    if not thread_id or not client:
        return

    runs = await client.beta.threads.runs.list(thread_id=thread_id)
    for run in runs.data:
        if run.status not in ["completed", "cancelled", "expired"]:
            with suppress(Exception):
                await client.beta.threads.runs.cancel(run_id=run.id, thread_id=thread_id)


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
    completed = False
    thread_id = cl.user_session.get("thread_id")
    async_openai_client = get_openai_client()

    if not thread_id or not async_openai_client:
        await cl.Message(content="An error occurred. Please try again later.").send()
        return

    try:
        message_files = await get_attachments(message, async_openai_client)

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

        completed = True

    # triggered when the user stops a chat
    except asyncio.exceptions.CancelledError:
        pass

    except Exception as e:
        await cl.Message(content=f"An error occurred: {e}").send()
        await cl.Message(content="Please try again in a moment.").send()
    finally:
        if not completed:
            await cancel_thread_run(thread_id)
