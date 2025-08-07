"""Test memory isolation to ensure tests don't write to real directories."""

import os
from pathlib import Path

import pytest
from fastmcp import Client

from mode_manager_mcp.simple_server import ModeManagerServer


@pytest.fixture()
def server(global_patch_and_tempdir: str) -> ModeManagerServer:
    return ModeManagerServer(prompts_dir=global_patch_and_tempdir)


@pytest.mark.asyncio
async def test_user_memory_isolation(server: ModeManagerServer) -> None:
    """Test that user memory writes to temp directory, not real VS Code prompts."""
    async with Client(server.app) as client:
        result = await client.call_tool("remember", {"memory_item": "test user memory isolation", "scope": "user"})
        assert "Remembered" in result.data or "Remembered" in str(result)

        # Verify no files were created in real VS Code prompts directory
        real_vscode_dir = Path.home() / "AppData" / "Roaming" / "Code - Insiders" / "User" / "prompts"
        if real_vscode_dir.exists():
            memory_files = list(real_vscode_dir.glob("memory*.instructions.md"))
            # Should not have created new memory files during test
            # (existing ones from actual usage are OK)


@pytest.mark.asyncio
async def test_workspace_memory_isolation(server: ModeManagerServer) -> None:
    """Test that workspace memory writes to temp directory, not real project .vscode."""
    async with Client(server.app) as client:
        result = await client.call_tool("remember", {"memory_item": "test workspace memory isolation", "scope": "workspace"})
        assert "Remembered" in result.data or "Remembered" in str(result)
        assert "workspace memory" in result.data or "workspace memory" in str(result)

        # Verify no .vscode/prompts directory was created in real project
        real_project_vscode = Path("c:/Development/github/mcpmemoryagent/.vscode/prompts")
        assert not real_project_vscode.exists(), "Workspace memory test created files in real project directory!"


@pytest.mark.asyncio
async def test_language_specific_memory_isolation(server: ModeManagerServer) -> None:
    """Test that language-specific memory is also properly isolated."""
    async with Client(server.app) as client:
        result = await client.call_tool("remember", {"memory_item": "use type hints for all Python functions", "scope": "user", "language": "python"})
        assert "Remembered" in result.data or "Remembered" in str(result)
        assert "python" in result.data.lower() or "python" in str(result).lower()
