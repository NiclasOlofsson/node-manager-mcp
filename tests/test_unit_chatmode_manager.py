import tempfile
from typing import Generator
from unittest.mock import patch

import pytest

from mode_manager_mcp.chatmode_manager import ChatModeManager


@pytest.fixture
def temp_prompts_dir() -> Generator[str, None, None]:
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch(
            "mode_manager_mcp.path_utils.get_vscode_prompts_directory",
            return_value=temp_dir,
        ):
            yield temp_dir


def test_chatmode_manager_create_and_delete(temp_prompts_dir: str) -> None:
    cm = ChatModeManager(prompts_dir=temp_prompts_dir)
    filename = "unit_test.chatmode.md"
    assert cm.create_chatmode(filename, "desc", "content", ["tool1"]) is True
    assert cm.delete_chatmode(filename) is True


def test_chatmode_manager_format_and_frontmatter(temp_prompts_dir: str) -> None:
    cm = ChatModeManager(prompts_dir=temp_prompts_dir)
    filename = "format_test.chatmode.md"
    description = "Test chatmode description"
    content = "# Chatmode Test\nThis is a test chatmode file."
    tools = ["toolA", "toolB"]
    assert cm.create_chatmode(filename, description, content, tools) is True

    # Read back and check format
    result = cm.get_chatmode(filename)
    frontmatter = result["frontmatter"]
    file_content = result["content"]

    # Check frontmatter keys
    assert "description" in frontmatter
    assert frontmatter["description"] == description
    assert "tools" in frontmatter
    assert frontmatter["tools"] == tools

    # Check markdown content starts correctly
    assert file_content == content
    assert "This is a test chatmode file." in file_content

    # Clean up
    assert cm.delete_chatmode(filename) is True
