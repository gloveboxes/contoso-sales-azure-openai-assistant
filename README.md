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

Review the [Deploy a containerized Flask or FastAPI web app on Azure App Service](https://learn.microsoft.com/en-us/azure/developer/python/tutorial-containerize-simple-web-app-for-app-service?tabs=web-app-fastapi)

1. Clone the repository

    ```shell
    git clone https://github.com/gloveboxes/contoso-sales-azure-openai-assistant.git
    ```

2. Change directory to the project folder

    ```shell
    cd contoso-sales-azure-openai-assistant
    ```

3. Open the project in Visual Studio Code

    ```shell
    code .
    ```

4. You'll be prompted to open in a Dev Container. Select `Reopen in Container`

5. Open the terminal in VS Code

6. Export the following environment variables

    Set these deployment variables in your terminal

    ```shell
    export RESOURCE_GROUP_NAME=<value>
    export RESOURCE_GROUP_LOCATION=<value>      # Suggest a location near the model location, use az account list-locations --query "[].name" --output tsv
    export APP_SERVICE_PLAN_NAME=<value>
    export WEB_APP_NAME=<value>
    export CONTAINER_REGISTRY_NAME=<value>
    export CONTAINER_IMAGE_NAME=<value>
    export SUBSCRIPTION_ID=$(az account show --query id --output tsv)
    ```

    Set these Azure OpenAI environment variables in your terminal

    ```shell
    export AZURE_OPENAI_RESOURCE_NAME=<value>   # This should be the Azure AI Proxy endpoint for the event
    export AZURE_OPENAI_LOCATION=<value>        # eg swedencentral
    export AZURE_OPENAI_DEPLOYMENT=<value>      # eg gpt-4o
    export AZURE_OPENAI_API_VERSION=<value>     # eg 2024-05-01-preview
    ```

    Set the following application specific environment variables in your terminal

    ```shell
    export AZURE_OPENAI_ENDPOINT=<value>        # This should be the Azure AI Proxy endpoint for the event
    export LITERAL_API_KEY=<value>              # Optional, go to Literal AI https://cloud.getliteral.ai/, create a project and go to Settings to get your API key.
    export CHAINLIT_AUTH_SECRET=$(chainlit create-secret | cut -d'"' -f2)
    export AZURE_OPENAI_ASSISTANT_ID=<value>
    ```

## Create the Azure resources

1. Create a resource group

    ```shell
    az group create --name $RESOURCE_GROUP_NAME --location $RESOURCE_GROUP_LOCATION
    ```

2. Create a container registry

    ```shell
    az acr create --resource-group $RESOURCE_GROUP_NAME --name $CONTAINER_REGISTRY_NAME --sku Basic
    ```

3. Create an App Service plan

    ```shell
    az appservice plan create --name $YOUR_APP_SERVICE_PLAN_NAME --resource-group $RESOURCE_GROUP_NAME --sku B1 --is-linux
    ```

## Deploy the Azure OpenAI resource

1. Deploy an Azure OpenAI resource

    ```shell
    az cognitiveservices account create \
    --name $AZURE_OPENAI_RESOURCE_NAME \
    --resource-group $RESOURCE_GROUP_NAME \
    --kind OpenAI \
    --sku S0 \
    --location $AZURE_OPENAI_LOCATION
    ```

2. Deploy an Azure OpenAI Model

    ```shell
    az cognitiveservices account deployment create \
    --resource-group $RESOURCE_GROUP_NAME \
    --name $AZURE_OPENAI_RESOURCE_NAME \
    --deployment-name $AZURE_OPENAI_DEPLOYMENT \
    --model $AZURE_OPENAI_DEPLOYMENT \
    --model-version latest
    ```

## Deploy the web app

1. Build the container image

    From VS Code terminal, run the following command to build the container image. This will build the container image in Azure and push to your Azure Container Registry.

    ```shell
    az acr build --resource-group $RESOURCE_GROUP_NAME --registry $CONTAINER_REGISTRY_NAME --image $CONTAINER_IMAGE_NAME .
    ```

2. Create the web app

    ```shell
    az webapp create --resource-group $RESOURCE_GROUP_NAME \
    --plan $YOUR_APP_SERVICE_PLAN_NAME \
    --name $WEB_APP_NAME \
    --assign-identity [system] \
    --role AcrPull \
    --scope /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME \
    --acr-use-identity --acr-identity [system] \
    --container-image-name $CONTAINER_IMAGE_NAME
    ```

3. Set environment variables

    ```shell
    az webapp config appsettings set --resource-group $RESOURCE_GROUP_NAME \
    --name contoso-sales \
    --settings \
        AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT \
        AZURE_OPENAI_API_VERSION=$AZURE_OPENAI_API_VERSION \
        AZURE_OPENAI_DEPLOYMENT=$AZURE_OPENAI_DEPLOYMENT \
        LITERAL_API_KEY=$LITERAL_API_KEY \
        CHAINLIT_AUTH_SECRET=$CHAINLIT_AUTH_SECRET \
        AZURE_OPENAI_ASSISTANT_ID=$AZURE_OPENAI_ASSISTANT_ID
    ```
