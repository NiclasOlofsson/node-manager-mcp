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
