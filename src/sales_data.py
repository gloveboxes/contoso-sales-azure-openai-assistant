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
        db_uri = f"file:{'src/' if env == 'development' else ''}{DATA_BASE}?mode=ro"

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

    async def async_fetch_sales_data_using_sqlite_query(self: "SalesData", query: str) -> QueryResults:
        """
        This function is used to answer user questions about Contoso sales data by executing SQLite queries against the database.

        :param sqlite_query: The input should be a well-formed SQLite query to extract information based on the user's question. The query result will be returned as plain text, not in JSON format.
        :return: A QueryResults object containing the query results in both display and JSON formats.
        :rtype: QueryResults
        """

        data_results = QueryResults()

        try:
            # Perform the query asynchronously
            async with self.conn.execute(query) as cursor:
                rows = await cursor.fetchall()
                columns = [description[0] for description in cursor.description]

            if not rows:  # No need to create DataFrame if there are no rows
                data_results.display_format = "The query returned no results. Try a different query."
                data_results.json_format = ""
            else:
                # Only create DataFrame if there are rows
                data = pd.DataFrame(rows, columns=columns)
                data_results.display_format = data.to_string(index=False)
                data_results.json_format = data.to_json(index=False, orient="split")

        except Exception as e:
            error_message = f"Query failed with error: {e}"
            data_results.display_format = error_message
            data_results.json_format = json.dumps({"error": str(e), "query": query})

        return data_results
