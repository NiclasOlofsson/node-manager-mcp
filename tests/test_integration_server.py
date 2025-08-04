import pytest
from fastmcp import Client

from mode_manager_mcp.simple_server import ModeManagerServer


# The session-scoped fixture in conftest.py yields the temp prompts directory.
@pytest.fixture()
def server(global_patch_and_tempdir: str) -> ModeManagerServer:
    return ModeManagerServer(prompts_dir=global_patch_and_tempdir)


@pytest.mark.asyncio
async def test_remember_integration(server: ModeManagerServer) -> None:
    async with Client(server.app) as client:
        result = await client.call_tool("remember", {"memory_item": "integration test memory"})
        assert "Remembered" in result.data or "Remembered" in str(result)


@pytest.mark.asyncio
async def test_browse_library_integration(server: ModeManagerServer) -> None:
    async with Client(server.app) as client:
        result = await client.call_tool("browse_mode_library")
        assert "Library" in result.data or "Library" in str(result)


@pytest.mark.asyncio
async def test_get_prompts_directory_integration(server: ModeManagerServer) -> None:
    async with Client(server.app) as client:
        result = await client.call_tool("get_prompts_directory")
        assert "prompts" in result.data.lower() or "prompts" in str(result).lower()
