import os
from pathlib import Path

import pytest
from fastmcp import Client

from mode_manager_mcp.path_utils import get_vscode_prompts_directory
from mode_manager_mcp.simple_server import ModeManagerServer


@pytest.fixture(scope="module")
def server() -> ModeManagerServer:
    os.environ["MCP_CHATMODE_READ_ONLY"] = "false"
    s = ModeManagerServer()
    return s


@pytest.mark.asyncio
async def test_create_chatmode_endpoint(server: ModeManagerServer) -> None:
    async with Client(server.app) as client:
        result = await client.call_tool(
            "create_chatmode",
            {
                "filename": "func_test.chatmode.md",
                "description": "desc",
                "content": "content",
                "tools": "tool1,tool2",
            },
        )
        assert "Successfully created" in result.data or "Successfully created" in str(
            result
        )


@pytest.mark.asyncio
async def test_delete_chatmode_endpoint(server: ModeManagerServer) -> None:
    async with Client(server.app) as client:
        result = await client.call_tool(
            "delete_chatmode", {"filename": "func_test.chatmode.md"}
        )
        assert "Successfully deleted" in result.data or "Successfully deleted" in str(
            result
        )


@pytest.mark.asyncio
async def test_create_instruction_endpoint(server: ModeManagerServer) -> None:
    async with Client(server.app) as client:
        result = await client.call_tool(
            "create_instruction",
            {
                "instruction_name": "func_test.instructions.md",
                "description": "desc",
                "content": "content",
            },
        )
        assert "Successfully created" in result.data or "Successfully created" in str(
            result
        )


@pytest.mark.asyncio
async def test_delete_instruction_endpoint(server: ModeManagerServer) -> None:
    async with Client(server.app) as client:
        result = await client.call_tool(
            "delete_instruction", {"instruction_name": "func_test.instructions.md"}
        )
        assert "Successfully deleted" in result.data or "Successfully deleted" in str(
            result
        )
