import os
import tempfile
from typing import Generator
from unittest.mock import patch

import pytest


@pytest.fixture(scope="session", autouse=True)
def global_patch_and_tempdir() -> Generator[str, None, None]:
    temp_dir = tempfile.mkdtemp()
    prompts_dir = os.path.join(temp_dir, "prompts")
    os.makedirs(prompts_dir, exist_ok=True)
    os.environ["MCP_PROMPTS_DIRECTORY"] = prompts_dir
    os.environ["MCP_CHATMODE_READ_ONLY"] = "false"
    # Patch globally for all tests
    patcher = patch(
        "mode_manager_mcp.path_utils.get_vscode_prompts_directory",
        return_value=prompts_dir,
    )
    patcher.start()
    yield prompts_dir
    patcher.stop()
    import shutil

    shutil.rmtree(temp_dir)
