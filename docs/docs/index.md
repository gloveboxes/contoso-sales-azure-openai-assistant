# Contoso Sales Assistant

## Introduction to the Contoso Sales Assistant

You are a sales manager at Contoso, a multinational retail company that sells outdoor equipment. You need to analyze sales data to find trends, understand customer preferences, and make informed business decisions. To help you, Contoso has developed a conversational assistant that can answer questions about your sales data.

![Contoso Sales Assistant](media/persona.png)

## Solution Overview

The Contoso Sales Assistant is a conversational agent that can answer questions about sales data, generate charts, and create Excel files for further analysis.

The app is built with [Azure OpenAI GPT-4o](https://learn.microsoft.com/azure/ai-services/openai/concepts/models){:target="_blank"} , the [Azure OpenAI Assistants API](https://learn.microsoft.com/azure/ai-services/openai/concepts/assistants){:target="_blank"}  and the [Chainlit](https://docs.chainlit.io/){:target="_blank"}  Conversational AI  web framework.

The app uses a read-only SQLite Contoso Sales Database with 40,000 rows of synthetic data. When the app starts, it reads the sales database schema, product categories, product types, and reporting years, then adds this info to the Azure OpenAI Assistants API instruction context.

## Why use the Azure OpenAI Assistants API?

The Azure OpenAI Assistants API makes it easier to build Generative AI apps by simplifying key tasks:

1. Streamlined Development: It abstracts the complexities of integrating AI, allowing developers to focus on building features rather than managing the AI model.
2. Context Management: The API automatically handles conversation context, ensuring the AI provides relevant, coherent responses throughout interactions.
3. Scalability: It scales effortlessly, managing workloads and resources automatically to handle both small and large user bases.
4. Context Execution: The API lets you define and run context against an LLM, making it easier to perform tasks like data queries or code generation based on specific instructions.

### OpenAI Tools

The app uses the following Azure OpenAI tools:

1. **[Function Calling](https://learn.microsoft.com/azure/ai-services/openai/how-to/function-calling){:target="_blank"}**: To execute LLM generated SQL queries against the read-only SQLite database.
2. **[Code Interpreter](https://learn.microsoft.com/azure/ai-services/openai/how-to/code-interpreter?tabs=python){:target="_blank"}**: To run Python code to create visualizations like pie charts and bar charts, and generate Excel files for users to download for deeper analysis.
3. **[File Search](https://learn.microsoft.com/azure/ai-services/openai/how-to/file-search?tabs=python){:target="_blank"}**: To extend the assistant's knowledge with user loaded Contoso product datasheets.

### Best Practices

The app demonstrates best practices for creating a conversational agent with the Azure OpenAI Assistants API. The app is fully asynchronous, uses the FastAPI framework, and streams all responses to users in real-time.

### Extending

This solution can be easily adapted to support other scenarios, such as customer support, simply by changing the database and adjusting the Azure OpenAI Assistants API instructions to fit the new use case.

## The Contoso Sales Assistant Source Code

The source code is available in the [Contoso Sales Assistant built with the Azure OpenAI Assistant API and Chainlit](https://github.com/gloveboxes/contoso-sales-azure-openai-assistant){:target="_blank"}  repository.
