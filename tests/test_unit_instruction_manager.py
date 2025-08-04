import pytest

from mode_manager_mcp.instruction_manager import InstructionManager


@pytest.fixture
def prompts_dir(global_patch_and_tempdir: str) -> str:
    return global_patch_and_tempdir


def test_instruction_manager_create_and_delete(prompts_dir: str) -> None:
    im = InstructionManager(prompts_dir=prompts_dir)
    filename = "unit_test.instructions.md"
    assert im.create_instruction(filename, "desc", "content") is True
    assert im.delete_instruction(filename) is True


def test_instruction_manager_format_and_frontmatter(prompts_dir: str) -> None:
    im = InstructionManager(prompts_dir=prompts_dir)
    filename = "format_test.instructions.md"
    description = "Test description"
    content = "# Personal AI Memory\nThis is a test instruction file."
    assert im.create_instruction(filename, description, content) is True

    # Read back and check format
    result = im.get_instruction(filename)
    frontmatter = result["frontmatter"]
    file_content = result["content"]

    # Check frontmatter keys
    assert "applyTo" in frontmatter
    assert frontmatter["applyTo"] == "'**'"
    assert "description" in frontmatter
    assert frontmatter["description"] == description

    # Check markdown content starts correctly
    assert file_content.startswith("# Personal AI Memory")
    assert "This is a test instruction file." in file_content

    # Clean up
    assert im.delete_instruction(filename) is True
