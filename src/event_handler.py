import json
import logging
import re

import chainlit as cl
from literalai.helper import utc_now
from openai import AsyncAssistantEventHandler
from openai.types.beta.threads.runs.function_tool_call import FunctionToolCall
from typing_extensions import override

from sales_data import QueryResults

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

markdown_link_pattern = re.compile(r"\[(.*?)\]\s*\(\s*.*?\s*\)")
citation_pattern = re.compile(r"【.*?】")


class EventHandler(AsyncAssistantEventHandler):
    def __init__(self, function_map: dict, assistant_name: str, async_openai_client) -> None:
        super().__init__()
        self.current_message: cl.Message = None
        self.current_step: cl.Step = None
        self.current_tool_call = None
        self.assistant_name = assistant_name
        self.async_openai_client = async_openai_client
        self.function_map = function_map
        self.citations_index = 1

    async def get_file_annotation(self, file_path, annotation) -> tuple:
        file_name = annotation.text.split("/")[-1]
        content = await self.async_openai_client.files.content(file_path.file_id)
        return content.content, file_name

    @override
    async def on_text_created(self: "EventHandler", text) -> None:
        self.current_message = await cl.Message(author=self.assistant_name, content="").send()

    @override
    async def on_text_delta(self: "EventHandler", delta, snapshot):
        if snapshot.value and markdown_link_pattern.search(snapshot.value):
            await self.current_message.remove()
            snapshot.value = markdown_link_pattern.sub(r"\1", snapshot.value)
            await cl.Message(content=snapshot.value).send()
        if snapshot.value and citation_pattern.search(snapshot.value):
            await self.current_message.stream_token(delta.value)
            snapshot.value = citation_pattern.sub(f"[{self.citations_index}]", snapshot.value)
            await self.current_message.stream_token(f"[{self.citations_index}]")
            self.citations_index += 1
        elif delta.value:
            await self.current_message.stream_token(delta.value)

    @override
    async def on_text_done(self: "EventHandler", text: str) -> None:
        citations = []
        index = 0
        for annotation in text.annotations:
            if file_citation := getattr(annotation, "file_citation", None):
                cited_file = await self.async_openai_client.files.retrieve(file_citation.file_id)
                index += 1
                citations.append(f"[{index}] from {cited_file.filename}")

            elif file_path := getattr(annotation, "file_path", None):
                format_text, file_name = await self.get_file_annotation(file_path, annotation)
                elements = [
                    cl.File(
                        name=file_name,
                        content=format_text,
                        display="inline",
                    ),
                ]
                await cl.Message(content="", elements=elements).send()

        if citations:
            await cl.Message(content="\n".join(citations)).send()

        await self.current_message.update()

    @override
    async def on_tool_call_created(self: "EventHandler", tool_call: FunctionToolCall) -> None:
        if tool_call.type == "code_interpreter":
            self.current_tool_call = tool_call.id
            self.current_step = cl.Step(name=tool_call.type, type="tool")
            self.current_step.language = "python"
            self.current_step.created_at = utc_now()
            await self.current_step.send()

    @override
    async def on_tool_call_delta(self, delta, snapshot):
        if delta.type == "code_interpreter":
            if snapshot.id != self.current_tool_call:
                self.current_tool_call = snapshot.id
                self.current_step = cl.Step(name=delta.type, type="tool")
                self.current_step.language = "python"
                self.current_step.start = utc_now()
                await self.current_step.send()

            if delta.code_interpreter.input:
                await self.current_step.stream_token(delta.code_interpreter.input)
            if delta.code_interpreter.outputs:
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        pass

    async def on_image_file_done(self, image_file) -> None:
        image_id = image_file.file_id
        response = await self.async_openai_client.files.with_raw_response.content(image_id)
        image_element = cl.Image(name=image_id, content=response.content, display="inline", size="large")
        await self.async_openai_client.files.delete(image_id)
        if not self.current_message.elements:
            self.current_message.elements = []
        self.current_message.elements.append(image_element)
        await self.current_message.update()

    async def update_chainlit_function_ui(self, language: str, tool_call, result: QueryResults) -> None:
        # Update the UI with the step function output
        current_step = cl.Step(name="function", type="tool")
        current_step.language = language
        await current_step.stream_token(f"Function Name: {tool_call.function.name}\n")
        await current_step.stream_token(f"Function Arguments: {tool_call.function.arguments}\n\n")
        await current_step.stream_token(result.display_format)
        current_step.start = utc_now()
        await current_step.send()
        self.current_message = await cl.Message(author=self.assistant_name, content="").send()

    @override
    async def on_tool_call_done(self, tool_call: FunctionToolCall) -> None:
        """This method is called when a tool call is done."""
        """ Parallel tool calling is enabled by default and it's important to iterate through the tool calls. """

        if tool_call.type == "function" and self.current_run.status == "requires_action":
            tool_calls = self.current_run.required_action.submit_tool_outputs.tool_calls
            function_tool_calls = [call for call in tool_calls if call.type == "function"]
            tool_outputs = []

            for submit_tool_call in function_tool_calls:
                function = self.function_map.get(submit_tool_call.function.name)

                try:
                    arguments = json.loads(submit_tool_call.function.arguments)
                    result: QueryResults = await function(arguments)
                except json.JSONDecodeError as e:
                    result = QueryResults(
                        display_format=submit_tool_call.function.arguments,
                        json_format=str(e),
                    )

                tool_outputs.append({"tool_call_id": submit_tool_call.id, "output": result.json_format})
                await self.update_chainlit_function_ui("sql", submit_tool_call, result)

            if tool_outputs:
                async with self.async_openai_client.beta.threads.runs.submit_tool_outputs_stream(
                    thread_id=self.current_run.thread_id,
                    run_id=self.current_run.id,
                    tool_outputs=tool_outputs,
                    event_handler=EventHandler(
                        self.function_map,
                        self.assistant_name,
                        self.async_openai_client,
                    ),
                ) as stream:
                    await stream.until_done()

                await self.current_message.update()

        elif tool_call.type == "code_interpreter":
            self.current_step.end = utc_now()
            await self.current_step.update()
        elif tool_call.type == "file_search":
            pass
