# Contoso Sales Assistant

## Introduction to the Contoso Sales Assistant

You are a sales manager at Contoso, a multinational retail company that sells outdoor equipment. You need to analyze sales data to find trends, understand customer preferences, and make informed business decisions. To help you, Contoso has developed a conversational assistant that can answer questions about your sales data.

![Contoso Sales Assistant](media/persona.png)

## Solution Overview

The app is built using the [Azure OpenAI Assistants API](https://learn.microsoft.com/azure/ai-services/openai/concepts/assistants) and [Chainlit](https://docs.chainlit.io/), with the backend powered by the Azure OpenAI Assistants API and app is written in Python. It demonstrates best practices for creating a conversational agent with this API. To enhance performance, the app is fully asynchronous, uses the FastAPI framework, and streams all responses to users in real-time.

The demo uses a SQLite Contoso Sales Database with 40,000 rows of synthetic data. When the app starts, it reads the schema, product categories, product types, and reporting years, then adds this info to the Azure OpenAI Assistants API instruction context.

With this setup, the Azure OpenAI GPT-4 LLM and Assistants API can answer questions about Contoso’s sales data, generate SQL queries, and run them on the read-only SQLite database using function calls. The LLM and Code Interpreter can also run Python code to create visualizations, such as pie charts and tables, and generate Excel files for users to download for further analysis.

_This solution can be easily adapted to support other scenarios, such as customer support, simply by changing the database and adjusting the Azure OpenAI Assistants API instructions to fit the new use case._

## The Contoso Sales Assistant Source Code

The demo source code is available in the [Contoso Sales Assistant built with the Azure OpenAI Assistant API and Chainlit](https://github.com/gloveboxes/contoso-sales-azure-openai-assistant) repository.

### Security Concerns

A common concern with the demo scenario is security, particularly the risks of SQL injection or malicious attempts to drop the database. While these concerns are valid, they can easily be mitigated by setting the database access rights. For SQLite, this involves configuring the database as read-only. For a Database Service such as Postgres or Azure SQL, you would assign the application a read-only (Select) role. Additionally, running the application in a secure environment provides an extra layer of protection.

In enterprise scenarios, data is extracted and transformed from transactional systems into a read-only database or data warehouse with a user friendly schema. This approach ensures the data is secure, optimized for performance, and that the application has read-only access to the data.
