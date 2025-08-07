import os
import tempfile
from typing import Generator
from unittest.mock import patch

import pytest


@pytest.fixture(scope="session", autouse=True)
def global_patch_and_tempdir() -> Generator[str, None, None]:
    temp_dir = tempfile.mkdtemp()
    prompts_dir = os.path.join(temp_dir, "prompts")
    # Create a mock workspace directory inside temp_dir
    mock_workspace_dir = os.path.join(temp_dir, "mock_workspace")
    os.makedirs(prompts_dir, exist_ok=True)
    os.makedirs(mock_workspace_dir, exist_ok=True)

    os.environ["MCP_PROMPTS_DIRECTORY"] = prompts_dir
    os.environ["MCP_CHATMODE_READ_ONLY"] = "false"

    # Patch globally for all tests
    vscode_patcher = patch(
        "mode_manager_mcp.path_utils.get_vscode_prompts_directory",
        return_value=prompts_dir,
    )
    # Patch os.getcwd() specifically in the instruction_manager module
    # This ensures workspace memory uses temp directory instead of real project dir
    getcwd_patcher = patch(
        "mode_manager_mcp.instruction_manager.os.getcwd",
        return_value=mock_workspace_dir,
    )

    vscode_patcher.start()
    getcwd_patcher.start()

    yield prompts_dir

    vscode_patcher.stop()
    getcwd_patcher.stop()

    import shutil

    shutil.rmtree(temp_dir)
