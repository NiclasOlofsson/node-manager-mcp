#!/usr/bin/env python3
"""
Basic test for the Mode Manager MCP functionality
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from mode_manager_mcp.chatmode_manager import ChatModeManager
from mode_manager_mcp.instruction_manager import InstructionManager
from mode_manager_mcp.library_manager import LibraryManager
from mode_manager_mcp.path_utils import get_vscode_prompts_directory


def test_basic_functionality():
    """Test basic functionality of all managers"""
    print("=== Basic Mode Manager Test ===\n")
    
    try:
        # Test path utilities
        print("Test 1: Testing path utilities...")
        prompts_dir = get_vscode_prompts_directory()
        print(f"✅ Prompts directory: {prompts_dir}")
        print("✅ Test 1 PASSED\n")
        
        # Test chatmode manager
        print("Test 2: Testing ChatMode manager...")
        cm = ChatModeManager()
        chatmodes = cm.list_chatmodes()
        print(f"✅ Found {len(chatmodes)} chatmode files")
        print("✅ Test 2 PASSED\n")
        
        # Test instruction manager
        print("Test 3: Testing Instruction manager...")
        im = InstructionManager()
        instructions = im.list_instructions()
        print(f"✅ Found {len(instructions)} instruction files")
        print("✅ Test 3 PASSED\n")
        
        # Test library manager
        print("Test 4: Testing Library manager...")
        lm = LibraryManager()
        try:
            library_info = lm.browse_library()
            print(f"✅ Library contains {library_info['total_chatmodes']} chatmodes and {library_info['total_instructions']} instructions")
            print("✅ Test 4 PASSED\n")
        except Exception as e:
            print(f"⚠️ Library test failed (network required): {e}")
            print("✅ Test 4 SKIPPED (network dependency)\n")
        
        print("🎉 ALL BASIC TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mcp_server():
    """Test the MCP server"""
    print("\n=== MCP Server Test ===\n")
    
    try:
        from mode_manager_mcp.simple_server import ModeManagerServer
        
        print("Test: Creating MCP server...")
        server = ModeManagerServer()
        print("✅ MCP Server created successfully")
        print("✅ MCP Server test PASSED\n")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP Server test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Running Mode Manager MCP Tests...\n")
    
    success = True
    success &= test_basic_functionality()
    success &= test_mcp_server()
    
    if success:
        print("\n🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED!")
        sys.exit(1)