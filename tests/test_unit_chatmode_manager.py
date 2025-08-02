import pytest

from mode_manager_mcp.chatmode_manager import ChatModeManager


@pytest.fixture
def prompts_dir(global_patch_and_tempdir: str) -> str:
    return global_patch_and_tempdir


def test_chatmode_manager_create_and_delete(prompts_dir: str) -> None:
    cm = ChatModeManager(prompts_dir=prompts_dir)
    filename = "unit_test.chatmode.md"
    assert cm.create_chatmode(filename, "desc", "content", ["tool1"]) is True
    assert cm.delete_chatmode(filename) is True


def test_chatmode_manager_format_and_frontmatter(prompts_dir: str) -> None:
    cm = ChatModeManager(prompts_dir=prompts_dir)
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
