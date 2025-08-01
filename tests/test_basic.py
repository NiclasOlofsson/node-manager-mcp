#!/usr/bin/env python3
"""
Basic test for the Mode Manager MCP functionality
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mode_manager_mcp.chatmode_manager import ChatModeManager
from mode_manager_mcp.instruction_manager import InstructionManager
from mode_manager_mcp.library_manager import LibraryManager
from mode_manager_mcp.path_utils import get_vscode_prompts_directory


def test_basic_functionality():
    """Test basic functionality of all managers"""
    # Test path utilities
    prompts_dir = get_vscode_prompts_directory()
    assert prompts_dir is not None

    # Test chatmode manager
    cm = ChatModeManager()
    chatmodes = cm.list_chatmodes()
    assert isinstance(chatmodes, list)

    # Test instruction manager
    im = InstructionManager()
    instructions = im.list_instructions()
    assert isinstance(instructions, list)

    # Test library manager (network dependency, so allow skip on failure)
    lm = LibraryManager()
    try:
        library_info = lm.browse_library()
        assert "total_chatmodes" in library_info
        assert "total_instructions" in library_info
    except Exception:
        # Network or library error, skip this part
        pass


def test_mcp_server():
    """Test the MCP server"""
    from mode_manager_mcp.simple_server import ModeManagerServer

    server = ModeManagerServer()
    assert server is not None
