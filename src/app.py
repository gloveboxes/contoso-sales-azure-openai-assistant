import asyncio
import logging
import os
from contextlib import suppress
from pathlib import Path
from typing import Any, Callable, Dict, Set

import chainlit as cl
import openai
from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import (
    AsyncFunctionTool,
    AsyncToolSet,
    CodeInterpreterTool,
)
from azure.identity import DefaultAzureCredential
from chainlit.config import config
from dotenv import load_dotenv
from openai import AsyncAzureOpenAI, AzureOpenAI

from event_handler import EventHandler
from sales_data import SalesData

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv("src/.env", override=True)

AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_ASSISTANT_ID = os.environ.get("AZURE_OPENAI_ASSISTANT_ID")
API_DEPLOYMENT_NAME = os.getenv("API_DEPLOYMEMT_NAME")
ASSISTANT_PASSWORD = os.getenv("ASSISTANT_PASSWORD")
PROJECT_CONNECTION_STRING = os.getenv("PROJECT_CONNECTION_STRING")

sales_data = SalesData()
cl.instrument_openai()
AGENT_READY = False
agent = None


async_project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=PROJECT_CONNECTION_STRING,
)


async_functions: Set[Callable[..., Any]] = {
    sales_data.async_fetch_sales_data_using_sqlite_query,
}

async_function_calling_tool = AsyncFunctionTool(async_functions)
code_interpreter_tool = CodeInterpreterTool()

code_interpreter_tool = CodeInterpreterTool()

toolset = AsyncToolSet()
toolset.add(async_function_calling_tool)
toolset.add(code_interpreter_tool)


@cl.password_auth_callback
async def auth_callback(username: str, password: str) -> cl.User | None:
    """Authenticate the user"""
    # Normally, you would check the username and password against a database.
    # Or use OAuth or custom provider for authentication.
    # See Chainlit documentation https://docs.chainlit.io/authentication/overview
    if (username, password) == ("sales@contoso.com", ASSISTANT_PASSWORD):
        return cl.User(identifier="sales@contoso.com", metadata={"role": "sales", "provider": "credentials"})
    return None


async def initialize() -> None:
    """Initialize the assistant with the sales data schema and instructions."""
    global AGENT_READY, agent
    if AGENT_READY:
        return

    await sales_data.connect()
    database_schema_string = await sales_data.get_database_info()

    instructions = {
        "You are a polite, professional assistant specializing in Contoso sales data analysis. Provide clear, concise explanations.",
        "Use the `ask_database` function for sales data queries, defaulting to aggregated data unless a detailed breakdown is requested. The function returns JSON data.",
        f"Reference the following SQLite schema for the sales database: {
            database_schema_string}.",
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

    try:
        agent = async_project_client.agents.create_agent(
            model=API_DEPLOYMENT_NAME,
            name="Contoso Sales Assistant",
            instructions="\n".join(instructions),
            toolset=toolset,
        )
        print(f"Created agent, ID: {agent.id}")

        config.ui.name = agent.name
        AGENT_READY = True
    except openai.NotFoundError as e:
        logger.error("Assistant not found: %s", str(e))
    except Exception as e:
        logger.error("An error occurred initializing the assistant: %s", str(e))


@cl.set_starters
async def set_starters() -> list[cl.Starter]:
    """Set the starters for the assistant"""
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


async def get_thread_id(async_project_client: AIProjectClient) -> str:
    """Get the thread ID for the conversation"""
    if thread := cl.user_session.get("thread_id"):
        return thread

    try:
        thread = await async_project_client.agents.create_thread()
        cl.user_session.set("thread_id", thread.id)
        return thread.id
    except Exception as e:
        await cl.Message(content=str(e)).send()
        return None


async def cancel_thread_run(thread_id: str) -> None:
    """Cancel all runs in a thread"""
    if not thread_id:
        return

    # Wait a moment for any pending runs to spin up for cleaner cancellation
    await asyncio.sleep(2)

    await async_project_client.agents.delete_thread(thread_id)

    
    # runs = await async_project_client.beta.threads.runs.list(thread_id=thread_id)
    # for run in runs.data:
    #     if run.status not in ["completed", "cancelled", "expired", "failed"]:
    #         with suppress(Exception):
    #             await client.beta.threads.runs.cancel(run_id=run.id, thread_id=thread_id)


async def get_attachments(message: cl.Message, async_openai_client: AsyncAzureOpenAI) -> Dict:
    """Upload attachments to the assistant"""
    pass
    # file_paths = [file.path for file in message.elements]
    # if not file_paths:
    #     return None

    # await cl.Message(content="Uploading files.").send()
    # message_files = []

    # for path in file_paths:
    #     with Path(path).open("rb") as file:
    #         uploaded_file = await async_openai_client.files.create(file=file, purpose="assistants")
    #         message_files.append({"file_id": uploaded_file.id, "tools": [{"type": "file_search"}]})

    # # Wait a moment for the uploaded files to become available
    # await asyncio.sleep(1)
    # await cl.Message(content="Uploading completed.").send()
    # return message_files


@cl.on_message
async def main(message: cl.Message) -> None:
    """Handle the conversation with the assistant"""
    completed = False

    if async_project_client is None:
        await cl.Message(content="An error occurred initializing the assistant.").send()
        logger.error("Assistant not initialized.")
        return

    await initialize()

    thread_id = await get_thread_id(async_project_client)

    if not thread_id:
        await cl.Message(content="A thread wa not successfully created.").send()
        logger.error("Thread not successfully created.")
        return

    try:
        # message_files = await get_attachments(message, async_openai_client)

        # Add a Message to the Thread
        # await async_openai_client.beta.threads.messages.create(
        #     thread_id=thread_id,
        #     role="user",
        #     content=message.content,
        #     attachments=message_files,
        # )

        message = await async_project_client.agents.create_message(
            thread_id=thread_id,
            role="user",
            content=message.content,
        )

        stream = await async_project_client.agents.create_stream(
            thread_id=thread_id,
            assistant_id=agent.id,
            event_handler=EventHandler(
                functions=functions, project_client=async_project_client),
            max_completion_tokens=4096,
            max_prompt_tokens=4096,
            temperature=0.2,
        )

        async with stream as s:
            await s.until_done()

        # Create and Stream a Run
        # async with async_openai_client.beta.threads.runs.stream(
        #     thread_id=thread_id,
        #     assistant_id=assistant.id,
        #     event_handler=EventHandler(
        #         function_map=function_map,
        #         assistant_name=assistant.name,
        #         async_openai_client=async_openai_client,
        #     ),
        #     temperature=0.2,
        # ) as stream:
        #     await stream.until_done()

        completed = True

    # triggered when the user stops a chat
    except asyncio.exceptions.CancelledError:
        pass

    except Exception as e:
        await cl.Message(content=f"An error occurred: {e}").send()
        await cl.Message(content="Please try again in a moment.").send()
        logger.error("An error calling the LLM occurred: %s", str(e))
    finally:
        if not completed:
            await cancel_thread_run(thread_id)
