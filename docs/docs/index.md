# Contoso Sales Assistant

## Introduction to the Contoso Sales Assistant

You are a sales manager at Contoso, a multinational retail company that sells outdoor equipment. You need to analyze sales data to find trends, understand customer preferences, and make informed business decisions. To help you, Contoso has developed a conversational assistant that can answer questions about your sales data.

![Contoso Sales Assistant](media/persona.png)

## Solution Overview

The Contoso Sales Assistant is a conversational agent that can answer questions about sales data, generate charts, and create Excel files for further analysis.

The app is built with [Azure OpenAI GPT-4o](https://learn.microsoft.com/azure/ai-services/openai/concepts/models), the [Azure OpenAI Assistants API](https://learn.microsoft.com/azure/ai-services/openai/concepts/assistants) and the [Chainlit](https://docs.chainlit.io/) Conversational AI  web framework.

The app uses a SQLite Contoso Sales Database with 40,000 rows of synthetic data. When the app starts, it reads the sales database schema, product categories, product types, and reporting years, then adds this info to the Azure OpenAI Assistants API instruction context.

### OpenAI Tools

The app uses the following Azure OpenAI tools:

1. **[Function Calling](https://learn.microsoft.com/azure/ai-services/openai/how-to/function-calling)**: To generate SQL queries and execute them against the read-only SQLIte database.
2. **[Code Interpreter](https://learn.microsoft.com/azure/ai-services/openai/how-to/code-interpreter?tabs=python)**: To run Python code to create visualizations like pie charts and tables, and generate Excel files for users to download.
3. **[File Search](https://learn.microsoft.com/azure/ai-services/openai/how-to/file-search?tabs=python)**: To extend the assistant's knowledge with Contoso product datasheets.

### Best Practices

The app demonstrates best practices for creating a conversational agent with the Azure OpenAI Assistants API. The app is fully asynchronous, uses the FastAPI framework, and streams all responses to users in real-time.

### Extending

This solution can be easily adapted to support other scenarios, such as customer support, simply by changing the database and adjusting the Azure OpenAI Assistants API instructions to fit the new use case.

## The Contoso Sales Assistant Source Code

The demo source code is available in the [Contoso Sales Assistant built with the Azure OpenAI Assistant API and Chainlit](https://github.com/gloveboxes/contoso-sales-azure-openai-assistant) repository.

### Security Concerns

A common concern with the demo scenario is security, particularly the risks of SQL injection or malicious attempts to drop the database. While these concerns are valid, they can easily be mitigated by setting the database access rights. 

For SQLite, this involves configuring the database as read-only. For a Database Service such as Postgres or Azure SQL, you would assign the application a read-only (Select) role. Additionally, running the application in a secure environment provides an extra layer of protection.

In enterprise scenarios, data is extracted and transformed from transactional systems into a read-only database or data warehouse with a user friendly schema. This approach ensures the data is secure, optimized for performance, and that the application has read-only access to the data.
