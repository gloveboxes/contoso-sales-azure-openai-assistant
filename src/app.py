import asyncio
import json
import logging
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv("env/.env", override=True)

AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_ASSISTANT_ID = os.environ.get("AZURE_OPENAI_ASSISTANT_ID")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_AI_PROXY_ENDPOINT = os.getenv("AZURE_AI_PROXY_ENDPOINT")
USER_PASSWORD = os.getenv("USER_PASSWORD")

sales_data = SalesData()
cl.instrument_openai()
ASSISTANT_READY = False

with AzureOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
) as sync_openai_client:
    assistant = sync_openai_client.beta.assistants.retrieve(assistant_id=AZURE_OPENAI_ASSISTANT_ID)

function_map: Dict[str, Callable[[Any], str]] = {
    "ask_database": lambda args: sales_data.ask_database(query=args.get("query")),
}


def get_openai_client() -> AsyncAzureOpenAI:
    """Get an instance of the OpenAI"""
    return AsyncAzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
    )


# async def authenticate_api_key(api_key: str):
#     url = f"{AZURE_AI_PROXY_ENDPOINT}/eventinfo"
#     headers = {"api-key": api_key}
#     async with httpx.AsyncClient() as client:
#         response = await client.post(url, headers=headers)
#     if response.status_code == 200:
#         return response.text
#     return None


@cl.password_auth_callback
async def auth_callback(username: str, password: str):
    """Authenticate the user"""
    # Fetch the user matching username from your database
    # and compare the hashed password with the value stored in the database
    if (username, password) == ("assistant", USER_PASSWORD):
        return cl.User(identifier="assistant", metadata={"role": "admin", "provider": "credentials"})
    return None

    # event_response = await authenticate_api_key(password)
    # if event_response:
    #     event_settings = json.loads(event_response)
    #     event_settings.update({"api_key": password})
    #     return cl.User(identifier=username, metadata=event_settings)
    # return None


async def initialize() -> None:
    """Initialize the assistant with the sales data schema and instructions."""
    global ASSISTANT_READY
    if ASSISTANT_READY:
        return

    await sales_data.connect()
    database_schema_string = await sales_data.get_database_info()

    instructions = {
        "You are a polite, professional assistant specializing in Contoso sales data analysis. Provide clear, concise explanations.",
        "Use the `ask_database` function for sales data queries, defaulting to aggregated data unless a detailed breakdown is requested. The function returns JSON data.",
        f"Reference the following SQLite schema for the sales database: {database_schema_string}.",
        "Use the `file_search` tool to retrieve product information from uploaded files when relevant. Prioritize Contoso sales database data over files when responding.",
        "For sales data inquiries, present results in markdown tables by default unless the user requests visualizations.",
        "For visualizations: 1. Write and test code in your sandboxed environment. 2. Use the user's language preferences for visualizations (e.g. chart labels). 3. Display successful visualizations or retry upon error.",
        "If asked for 'help,' suggest example queries (e.g., 'What was last quarter's revenue?' or 'Top-selling products in Europe?').",
        "Only use data from the Contoso sales database or uploaded files to respond. If the query falls outside the available data or your expertise, or you're unsure, reply with: I'm unable to assist with that. Please ask more specific questions about Contoso sales and products or contact IT for further help.",
        "If faced with aggressive behavior, calmly reply: 'I'm here to help with sales data inquiries. For other issues, please contact IT.'",
        "Tailor responses to the user's language preferences, including terminology, measurement units, currency, and formats.",
        "For download requests, respond with: 'The download link is provided below.'",
        "Do not include markdown links to visualizations in your responses.",
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
        # sync_openai_client = AzureOpenAI(
        #     azure_endpoint=AZURE_OPENAI_ENDPOINT,
        #     api_key=AZURE_OPENAI_API_KEY,
        #     api_version=AZURE_OPENAI_API_VERSION,
        # )

        # assistant = sync_openai_client.beta.assistants.retrieve(assistant_id=AZURE_OPENAI_ASSISTANT_ID)

        sync_openai_client.beta.assistants.update(
            assistant_id=assistant.id,
            name="Contoso Sales Assistant",
            model=AZURE_OPENAI_DEPLOYMENT,
            instructions=str(instructions),
            tools=tools_list,
        )

        config.ui.name = assistant.name

        ASSISTANT_READY = True

    except openai.NotFoundError as e:
        logger.error(f"Assistant not found: {e}")
        return
    except Exception as e:
        logger.error(f"An error occurred initializing the assistant: {e}")
        return


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


async def get_thread_id(async_openai_client) -> str:
    if thread := cl.user_session.get("thread_id"):
        return thread

    try:
        thread = await async_openai_client.beta.threads.create()
        cl.user_session.set("thread_id", thread.id)
        # await cl.Message(content="New thread created.").send()
        return thread.id
    except Exception as e:
        await cl.Message(content=str(e)).send()
        return None


async def cancel_thread_run(thread_id: str) -> None:
    """Cancel all runs in a thread"""
    client = get_openai_client()
    if not thread_id or not client:
        return

    # Wait a moment for any pending runs to spin up for cleaner cancellation
    await asyncio.sleep(2)
    runs = await client.beta.threads.runs.list(thread_id=thread_id)
    for run in runs.data:
        if run.status not in ["completed", "cancelled", "expired", "failed"]:
            with suppress(Exception):
                await client.beta.threads.runs.cancel(run_id=run.id, thread_id=thread_id)


async def get_attachments(message: cl.Message, async_openai_client: AsyncAzureOpenAI) -> Dict:
    """Upload attachments to the assistant"""
    file_paths = [file.path for file in message.elements]
    if not file_paths:
        return None

    await cl.Message(content="Uploading files.").send()
    message_files = []

    for path in file_paths:
        with Path(path).open("rb") as file:
            uploaded_file = await async_openai_client.files.create(file=file, purpose="assistants")
            message_files.append({"file_id": uploaded_file.id, "tools": [{"type": "file_search"}]})

    # Wait a moment for the uploaded files to become available
    await asyncio.sleep(1)
    await cl.Message(content="Uploading completed.").send()
    return message_files


@cl.on_message
async def main(message: cl.Message) -> None:
    """Handle the conversation with the assistant"""
    completed = False

    if assistant is None:
        await cl.Message(content="An error occurred initializing the assistant.").send()
        logger.error("Assistant not initialized.")
        return

    await initialize()

    async_openai_client = get_openai_client()
    thread_id = await get_thread_id(async_openai_client)

    if not thread_id:
        await cl.Message(content="A thread wa not successfully created.").send()
        logger.error("Thread not successfully created.")
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
        logger.error("An error calling the LLM occurred: %s", e)
    finally:
        if not completed:
            await cancel_thread_run(thread_id)
