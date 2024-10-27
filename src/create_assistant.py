import json
import os

import aiosqlite
import pandas as pd
from pydantic import BaseModel

DATA_BASE = "database/contoso-sales.db"


class QueryResults(BaseModel):
    display_format: str = ""
    json_format: str = ""


class SalesData:
    def __init__(self: "SalesData") -> None:
        self.conn = None

    async def connect(self: "SalesData") -> None:
        env = os.getenv("ENV", "development")
        if env == "development":
            db_uri = f"file:src/{DATA_BASE}?mode=ro"
        elif env == "production":
            db_uri = f"file:{DATA_BASE}?mode=ro"

        try:
            self.conn = await aiosqlite.connect(db_uri, uri=True)
            print("Database connection opened.")
        except aiosqlite.Error as e:
            print(f"An error occurred: {e}")
            self.conn = None

    async def close(self: "SalesData") -> None:
        if self.conn:
            await self.conn.close()
            print("Database connection closed.")

    async def __get_table_names(self: "SalesData") -> list:
        """Return a list of table names."""
        table_names = []
        async with self.conn.execute("SELECT name FROM sqlite_master WHERE type='table';") as tables:
            async for table in tables:
                if table[0] != "sqlite_sequence":
                    table_names.append(table[0])
        return table_names

    async def __get_column_info(self: "SalesData", table_name: str) -> list:
        """Return a list of tuples containing column names and their types."""
        column_info = []
        async with self.conn.execute(f"PRAGMA table_info('{table_name}');") as columns:
            async for col in columns:
                column_info.append(f"{col[1]}: {col[2]}")  # col[1] is the column name, col[2] is the column type
        return column_info

    async def __get_regions(self: "SalesData") -> list:
        """Return a list of unique regions in the database."""
        async with self.conn.execute("SELECT DISTINCT region FROM sales_data;") as regions:
            result = await regions.fetchall()
        return [region[0] for region in result]

    async def __get_product_types(self: "SalesData") -> list:
        """Return a list of unique product types in the database."""
        async with self.conn.execute("SELECT DISTINCT product_type FROM sales_data;") as product_types:
            result = await product_types.fetchall()
        return [product_type[0] for product_type in result]

    async def __get_product_categories(self: "SalesData") -> list:
        """Return a list of unique product categories in the database."""
        async with self.conn.execute("SELECT DISTINCT main_category FROM sales_data;") as product_categories:
            result = await product_categories.fetchall()
        return [product_category[0] for product_category in result]

    async def __get_reporting_years(self: "SalesData") -> list:
        """Return a list of unique reporting years in the database."""
        async with self.conn.execute("SELECT DISTINCT year FROM sales_data ORDER BY year;") as reporting_years:
            result = await reporting_years.fetchall()
        return [str(reporting_year[0]) for reporting_year in result]

    async def get_database_info(self: "SalesData") -> str:
        """Return a string containing the database schema information and common query fields."""
        table_dicts = []
        for table_name in await self.__get_table_names():
            columns_names = await self.__get_column_info(table_name)
            table_dicts.append({"table_name": table_name, "column_names": columns_names})

        database_info = "\n".join(
            [
                f"Table {table['table_name']} Schema: Columns: {', '.join(table['column_names'])}"
                for table in table_dicts
            ]
        )
        regions = await self.__get_regions()
        product_types = await self.__get_product_types()
        product_categories = await self.__get_product_categories()
        reporting_years = await self.__get_reporting_years()

        database_info += f"\nRegions: {', '.join(regions)}"
        database_info += f"\nProduct Types: {', '.join(product_types)}"
        database_info += f"\nProduct Categories: {', '.join(product_categories)}"
        database_info += f"\nReporting Years: {', '.join(reporting_years)}"
        database_info += "\n\n"

        return database_info


async def initialize():
    sales_data = SalesData()

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
        sync_openai_client = AzureOpenAI(
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=api_key,
            api_version=AZURE_OPENAI_API_VERSION,
        )

        assistant = sync_openai_client.beta.assistants.retrieve(assistant_id=assistant_id)

        sync_openai_client.beta.assistants.update(
            assistant_id=assistant.id,
            name="Contoso Sales Assistant",
            model=AZURE_OPENAI_DEPLOYMENT,
            instructions=str(instructions),
            tools=tools_list,
        )

        config.ui.name = assistant.name
        logger.info(f"Assistant initialized: {assistant.name}")

        return assistant
    except openai.NotFoundError as e:
        logger.error(f"Assistant not found: {e}")
        return None
    except Exception as e:
        logger.error(f"An error occurred initializing the assistant: {e}")
        return None
