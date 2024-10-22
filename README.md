# Contoso Sales Assistant Built with the Azure OpenAI Assistant API and Chainlit

## Documentation

See the full documentation at [Contoso Sales Assistant](https://gloveboxes.github.io/contoso-sales-azure-openai-assistant/)

<!-- ## Run

1. rename the `.env.example` file to `.env` and fill in the required values.
2. Select <kbd>F5</kbd> to start the bot in debugger mode.
3. From your browswer, navigate to `http://0.0.0.0/sales` to start the bot.

### [Optional] Get a Literal AI API key

> [!NOTE]
> Literal AI is an all in one observability, evaluation and analytics platform for building LLM apps.

Go to [Literal AI](https://cloud.getliteral.ai/), create a project and go to Settings to get your API key. -->

## Deploying on Azure

```shell
azd up
```

You'll be prompted for the following:

1. Chainlit Auth Secret: Run 'chainlit auth' to get your secret