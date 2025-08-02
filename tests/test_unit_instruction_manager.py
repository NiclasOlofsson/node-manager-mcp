import tempfile
from typing import Generator
from unittest.mock import patch

import pytest

from mode_manager_mcp.instruction_manager import InstructionManager


@pytest.fixture
def temp_prompts_dir() -> Generator[str, None, None]:
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch(
            "mode_manager_mcp.path_utils.get_vscode_prompts_directory",
            return_value=temp_dir,
        ):
            yield temp_dir


def test_instruction_manager_create_and_delete(temp_prompts_dir: str) -> None:
    im = InstructionManager(prompts_dir=temp_prompts_dir)
    filename = "unit_test.instructions.md"
    assert im.create_instruction(filename, "desc", "content") is True
    assert im.delete_instruction(filename) is True
