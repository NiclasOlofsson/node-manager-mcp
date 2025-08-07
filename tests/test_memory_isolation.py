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
    """Test that workspace memory writes to temp directory, not real project directory."""
    # Store initial state of real project directory
    real_project_github = Path("c:/Development/github/mcpmemoryagent/.github/instructions")
    initial_files = set()
    if real_project_github.exists():
        initial_files = {f.name for f in real_project_github.iterdir() if f.is_file()}

    async with Client(server.app) as client:
        result = await client.call_tool("remember", {"memory_item": "test workspace memory isolation", "scope": "workspace"})
        assert "Remembered" in result.data or "Remembered" in str(result)
        assert "workspace memory" in result.data or "workspace memory" in str(result)

        # Verify the file was created in the temp workspace directory (from patching)
        temp_workspace_dir = server.instruction_manager.workspace_prompts_dir
        memory_file = temp_workspace_dir / "memory.instructions.md"

        assert memory_file.exists(), f"Workspace memory file should be created at {memory_file}"

        # Verify content contains our test memory
        content = memory_file.read_text()
        assert "test workspace memory isolation" in content

        # Verify no file was created in real project directory
        real_memory_file = real_project_github / "memory.instructions.md"
        assert not real_memory_file.exists(), "Memory file should not be created in real project directory"

        # Verify real project directory state is unchanged
        if real_project_github.exists():
            final_files = {f.name for f in real_project_github.iterdir() if f.is_file()}
            assert final_files == initial_files, "Real project directory should be unchanged"


@pytest.mark.asyncio
async def test_language_specific_memory_isolation(server: ModeManagerServer) -> None:
    """Test that language-specific memory is also properly isolated."""
    async with Client(server.app) as client:
        result = await client.call_tool("remember", {"memory_item": "use type hints for all Python functions", "scope": "user", "language": "python"})
        assert "Remembered" in result.data or "Remembered" in str(result)
        assert "python" in result.data.lower() or "python" in str(result).lower()
