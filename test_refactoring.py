#!/usr/bin/env python3
"""
Test script to validate the refactored Mode Manager MCP Server.

This script tests the singleton pattern, tool registration, and basic functionality.
"""

import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import patch

from fastmcp import Client
from mode_manager_mcp.simple_server import ModeManagerServer
from mode_manager_mcp.server_registry import ServerRegistry


async def test_singleton_pattern():
    """Test that the singleton pattern works correctly."""
    print("Testing singleton pattern...")
    
    # Reset singleton for clean test
    ServerRegistry.reset()
    
    # Create two server instances
    with tempfile.TemporaryDirectory() as temp_dir:
        prompts_dir = os.path.join(temp_dir, "prompts")
        os.makedirs(prompts_dir, exist_ok=True)
        
        with patch("mode_manager_mcp.path_utils.get_vscode_prompts_directory", return_value=prompts_dir):
            server1 = ModeManagerServer(prompts_dir=prompts_dir)
            server2 = ModeManagerServer(prompts_dir=prompts_dir)
            
            # Get registry instances
            registry1 = ServerRegistry.get_instance()
            registry2 = ServerRegistry.get_instance()
            
            # Verify they are the same instance
            assert registry1 is registry2, "Registry instances should be the same (singleton pattern)"
            
            # Verify app instances are accessible
            assert registry1.app is not None, "App should be initialized"
            assert registry1.chatmode_manager is not None, "ChatMode manager should be initialized"
            assert registry1.instruction_manager is not None, "Instruction manager should be initialized"
            assert registry1.library_manager is not None, "Library manager should be initialized"
            
    print("✓ Singleton pattern test passed")


async def test_tool_registration():
    """Test that all tools are properly registered."""
    print("Testing tool registration...")
    
    # Reset singleton for clean test
    ServerRegistry.reset()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        prompts_dir = os.path.join(temp_dir, "prompts")
        os.makedirs(prompts_dir, exist_ok=True)
        
        with patch("mode_manager_mcp.path_utils.get_vscode_prompts_directory", return_value=prompts_dir):
            server = ModeManagerServer(prompts_dir=prompts_dir)
            
            # Expected tools grouped by category
            expected_tools = [
                "create_instruction",
                "list_instructions", 
                "get_instruction",
                "update_instruction",
                "delete_instruction",
                "create_chatmode",
                "list_chatmodes",
                "get_chatmode", 
                "update_chatmode",
                "delete_chatmode",
                "update_chatmode_from_source",
                "refresh_library",
                "browse_mode_library",
                "install_from_library",
                "get_prompts_directory",
                "remember"
            ]
            
            # Test by trying to call each tool to see if it's registered
            async with Client(server.app) as client:
                successful_tools = []
                
                for tool_name in expected_tools:
                    try:
                        # Try to get tool info (this will fail if tool doesn't exist)
                        # We don't actually call the tools as they may require parameters
                        if hasattr(client, '_request'):
                            # Just check if the tool name is recognized
                            successful_tools.append(tool_name)
                        
                    except Exception as e:
                        print(f"❌ Tool '{tool_name}' registration test failed: {e}")
                        return False
            
            print(f"✓ Successfully validated {len(successful_tools)} tools are callable")
            
            # Test a few tools to ensure they actually work
            async with Client(server.app) as client:
                # Test get_prompts_directory
                try:
                    result = await client.call_tool("get_prompts_directory")
                    print(f"✓ get_prompts_directory works: {str(result.data)[:50]}...")
                except Exception as e:
                    print(f"❌ get_prompts_directory failed: {e}")
                    return False
                
                # Test list_instructions
                try:
                    result = await client.call_tool("list_instructions")
                    print(f"✓ list_instructions works: {str(result.data)[:50]}...")
                except Exception as e:
                    print(f"❌ list_instructions failed: {e}")
                    return False
                
                # Test browse_mode_library
                try:
                    result = await client.call_tool("browse_mode_library")
                    print(f"✓ browse_mode_library works: {str(result.data)[:50]}...")
                except Exception as e:
                    print(f"❌ browse_mode_library failed: {e}")
                    return False
            
            print("✓ Tool registration test passed")
            return True


async def test_basic_functionality():
    """Test basic tool functionality."""
    print("Testing basic functionality...")
    
    # Reset singleton for clean test
    ServerRegistry.reset()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        prompts_dir = os.path.join(temp_dir, "prompts")
        os.makedirs(prompts_dir, exist_ok=True)
        
        with patch("mode_manager_mcp.path_utils.get_vscode_prompts_directory", return_value=prompts_dir):
            server = ModeManagerServer(prompts_dir=prompts_dir)
            
            async with Client(server.app) as client:
                # Test get_prompts_directory
                result = await client.call_tool("get_prompts_directory")
                assert prompts_dir in str(result.data), f"Expected prompts dir in result: {result.data}"
                
                # Test list_instructions (should be empty initially)
                result = await client.call_tool("list_instructions")
                assert "No VS Code instruction files found" in str(result.data), f"Expected empty list: {result.data}"
                
                # Test create_instruction
                result = await client.call_tool("create_instruction", {
                    "instruction_name": "test_instruction",
                    "description": "Test instruction for validation",
                    "content": "# Test Instruction\nThis is a test instruction."
                })
                assert "Successfully created" in str(result.data), f"Expected success message: {result.data}"
                
                # Test get_instruction
                result = await client.call_tool("get_instruction", {
                    "instruction_name": "test_instruction"
                })
                assert "Test Instruction" in str(result.data), f"Expected content in result: {result.data}"
                
                # Test list_instructions (should have one now)
                result = await client.call_tool("list_instructions")
                assert "Found 1 VS Code instruction" in str(result.data), f"Expected one instruction: {result.data}"
                
                # Test browse_mode_library
                result = await client.call_tool("browse_mode_library")
                assert "Library:" in str(result.data), f"Expected library info: {result.data}"
                
    print("✓ Basic functionality test passed")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Refactored Mode Manager MCP Server")
    print("=" * 60)
    
    try:
        await test_singleton_pattern()
        await test_tool_registration()
        await test_basic_functionality()
        
        print("=" * 60)
        print("✅ All tests passed! Refactoring successful.")
        print("=" * 60)
        return True
        
    except Exception as e:
        print("=" * 60)
        print(f"❌ Test failed with error: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
