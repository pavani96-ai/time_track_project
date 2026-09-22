import asyncio
import os
from pathlib import Path
from fastmcp import Client
from anthropic import Anthropic
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

async def on_progress(progress: float, total: float | None, message: str | None):
    print(f"  progress update: {progress}/{total} -- {message}")

async def elicitation_handler(message: str, response_type, params, context):
    """
    Called BY the server, through the client, whenever a tool calls
    ctx.elicit(). In a real app with a UI, this is where you'd show a
    real dialog box. For this demo, we print the question and auto-confirm.
    """
    print(f"\n[The server is asking]: {message}")
    print("[Auto-confirming for this demo -- swap this for real input() or a UI in your own client]")
    return True

def mcp_tools_to_anthropic_format(mcp_tools) -> list[dict]:
    """MCP describes a tool one way. Anthropic's API wants it described a
    slightly different way. This is the ONLY translation a framework-free
    agent loop actually needs to do by hand.
    """
    return [
        {"name": tool.name,
            "description": tool.description or "",
            "input_schema": tool.input_schema}
            for tool in mcp_tools
    ]

async def run_one_tool_call(mcp_client: Client, block) -> dict:
    print(f" -> calling {block.name} with {block.input}")

    result = await mcp_client.call_tool(block.name, block.input)

    print("MCP RESULT:", result)
    print("MCP RESULT CONTENT:", result.content)

    return {
        "type": "tool_result",
        "tool_use_id": block.id,
        "content": str(result.content)
    }
async def run_agent_loop(user_message: str):
    anthropic_client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    async with Client("main.py",elicitation_handler=elicitation_handler,timeout=30.0,progress_handler=on_progress, mode="legacy") as mcp_client:
        mcp_tools = await mcp_client.list_tools()
        anthropic_tools = mcp_tools_to_anthropic_format(mcp_tools)

        messages = [{"role":"user", "content": user_message}]

        while True :
            response = anthropic_client.messages.create(
                model = "claude-sonnet-4-5",
                max_tokens=1024,
                tools = anthropic_tools,
                messages=messages)

            if response.stop_reason != "tool_use":
                final_text = "".join(
                    block.text for block in response.content if block.type == "text"
                )
                print(f"Assistant: {final_text}")
                return final_text
            messages.append({"role":"assistant", "content":response.content})

            tool_results = [
                await run_one_tool_call(mcp_client, block)
                for block in response.content
                if block.type == "tool_use"
            ]

            messages.append({"role": "user", "content": tool_results})

if __name__ == "__main__":
    asyncio.run(run_agent_loop("Show me my time entries for today"))