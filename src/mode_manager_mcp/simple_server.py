"""
Mode Manager MCP Server Implementation.

This server provides tools for managing VS Code .chatmode.md and .instructions.md files
which define custom instructions and tools for GitHub Copilot.
"""

import datetime
import json
import logging
import os
import sys
from typing import Optional

from mcp.server import FastMCP

from .chatmode_manager import ChatModeManager
from .instruction_manager import INSTRUCTION_FILE_EXTENSION, InstructionManager
from .library_manager import LibraryManager
from .simple_file_ops import FileOperationError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModeManagerServer:
    """
    Mode Manager MCP Server.

    Provides tools for managing VS Code .chatmode.md and .instructions.md files.
    """

    def __init__(self, library_url: Optional[str] = None):
        """Initialize the server.

        Args:
            library_url: Custom URL for the Mode Manager MCP Library (optional)
        """
        self.app = FastMCP(
            name="Mode Manager MCP",
            instructions="""
            This server provides tools for managing VS Code prompt files and user memory.
            
            🧠 **PRIMARY FEATURE - User Memory Management:**
            - remember(memory_item): Store information in your personal AI memory for future conversations
            
            📂 **Additional Capabilities:**
            - Manage .chatmode.md and .instructions.md files for GitHub Copilot
            - Browse and install from the Mode Manager MCP Library
            - Auto-setup memory file in VS Code prompts directory
            
            💡 **Main Usage**: Use remember("information") to store anything you want AI assistants to remember about you.
            """,
        )
        self.chatmode_manager = ChatModeManager()
        self.instruction_manager = InstructionManager()

        # Allow library URL to be configured via parameter, environment variable, or use default
        final_library_url = (
            library_url
            or os.getenv("MCP_LIBRARY_URL")
            or "https://raw.githubusercontent.com/NiclasOlofsson/node-manager-mcp/refs/heads/main/library/memory-mode-library.json"
        )
        self.library_manager = LibraryManager(library_url=final_library_url)

        self.read_only = os.getenv("MCP_CHATMODE_READ_ONLY", "false").lower() == "true"

        # Register all tools
        self._register_tools()

        logger.info("Mode Manager MCP Server initialized")
        logger.info(f"Using library URL: {final_library_url}")
        if self.read_only:
            logger.info("Running in READ-ONLY mode")

    def _register_tools(self) -> None:
        """Register all MCP tools."""

        @self.app.tool()
        def remember(memory_item: str) -> str:
            """
            Store information in your personal AI memory for future conversations.

            This is the main tool for memory management. It automatically:
            - Sets up your memory file if it doesn't exist
            - Adds new memories to your personal instruction file
            - Maintains your memories in VS Code's prompts directory

            Args:
                memory_item: The information you want to remember (preferences, facts, context, etc.)

            Returns:
                Confirmation of what was remembered
            """
            if self.read_only:
                return "Error: Server is running in read-only mode"

            try:
                import datetime
                from pathlib import Path

                # Memory file location in VS Code prompts directory
                memory_filename = f"memory{INSTRUCTION_FILE_EXTENSION}"
                memory_path = self.instruction_manager.prompts_dir / memory_filename

                # Check if memory file exists
                if not memory_path.exists():
                    # Create initial memory file
                    initial_content = """# Personal AI Memory

This file contains information that I should remember about you and your preferences for future conversations.

## Memories

"""
                    success = self.instruction_manager.create_instruction(
                        memory_filename,
                        "Personal AI memory for conversations and preferences",
                        initial_content,
                    )

                    if not success:
                        return "Error: Failed to create memory file"

                    logger.info("Created new memory file for user")

                # Add the new memory item
                current_memory = self.instruction_manager.get_instruction(
                    memory_filename
                )
                current_content = current_memory["content"]

                # Add timestamp and new memory
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                new_memory_entry = f"- **{timestamp}**: {memory_item}\n"

                # Append to the memories section
                if "## Memories" in current_content:
                    # Add after the Memories header
                    updated_content = current_content.replace(
                        "## Memories\n", f"## Memories\n{new_memory_entry}"
                    )
                else:
                    # Add memories section if it doesn't exist
                    updated_content = (
                        current_content + f"\n## Memories\n{new_memory_entry}"
                    )

                # Update the memory file
                success = self.instruction_manager.update_instruction(
                    memory_filename, content=updated_content
                )

                if success:
                    return f"✅ Remembered: {memory_item}\\n\\n📁 Stored in: {memory_path}\\n\\n💡 This memory will be available to AI assistants when the memory instruction is active in VS Code."
                else:
                    return "Error: Failed to update memory file"

            except FileOperationError as e:
                return f"Error managing memory: {str(e)}"
            except Exception as e:
                return f"Unexpected error: {str(e)}"

        @self.app.tool()
        def list_chatmodes() -> str:
            """
            List all VS Code .chatmode.md files in the prompts directory.

            Returns:
                List of available chatmode files
            """
            try:
                chatmodes = self.chatmode_manager.list_chatmodes()

                if not chatmodes:
                    return "No VS Code chatmode files found in the prompts directory"

                result = f"Found {len(chatmodes)} VS Code chatmode(s):\\n\\n"
                for chatmode in chatmodes:
                    result += f"📄 {chatmode['name']}\\n"
                    result += f"   File: {chatmode['filename']}\\n"
                    if chatmode["description"]:
                        result += f"   Description: {chatmode['description']}\\n"
                    if chatmode["tools"]:
                        result += f"   Tools: {len(chatmode['tools'])} available\\n"
                    result += f"   Size: {chatmode['size']} bytes\\n"
                    if chatmode["content_preview"]:
                        result += (
                            f"   Preview: {chatmode['content_preview'][:100]}...\\n"
                        )
                    result += "\\n"

                return result

            except Exception as e:
                return f"Error listing VS Code chatmodes: {str(e)}"

        @self.app.tool()
        def get_chatmode(filename: str) -> str:
            """
            Get content of a specific VS Code chatmode file.

            Args:
                filename: Name of the .chatmode.md file

            Returns:
                Chatmode content with frontmatter and instructions
            """
            try:
                raw_content = self.chatmode_manager.get_raw_chatmode(filename)
                return raw_content

            except FileOperationError as e:
                return f"Error getting VS Code chatmode '{filename}': {str(e)}"
            except Exception as e:
                return (
                    f"Unexpected error getting VS Code chatmode '{filename}': {str(e)}"
                )

        @self.app.tool()
        def create_chatmode(
            filename: str, description: str, content: str, tools: Optional[str] = None
        ) -> str:
            """
            Create a new VS Code chatmode file.

            Args:
                filename: Name for the new .chatmode.md file
                description: Description of the chatmode
                content: Chatmode content/instructions
                tools: Comma-separated list of tools (optional)

            Returns:
                Success message or error
            """
            if self.read_only:
                return "Error: Server is running in read-only mode"

            try:
                # Parse tools if provided
                tools_list = None
                if tools:
                    tools_list = [
                        tool.strip() for tool in tools.split(",") if tool.strip()
                    ]

                success = self.chatmode_manager.create_chatmode(
                    filename, description, content, tools_list
                )

                if success:
                    return f"Successfully created VS Code chatmode: {filename}"
                else:
                    return f"Failed to create VS Code chatmode: {filename}"

            except FileOperationError as e:
                return f"Error creating VS Code chatmode '{filename}': {str(e)}"
            except Exception as e:
                return (
                    f"Unexpected error creating VS Code chatmode '{filename}': {str(e)}"
                )

        @self.app.tool()
        def update_chatmode(
            filename: str,
            description: Optional[str] = None,
            content: Optional[str] = None,
            tools: Optional[str] = None,
        ) -> str:
            """
            Update a VS Code chatmode file.

            Args:
                filename: Name of the .chatmode.md file
                description: New description (optional)
                content: New content/instructions (optional)
                tools: Comma-separated list of tools (optional)

            Returns:
                Success message or error
            """
            if self.read_only:
                return "Error: Server is running in read-only mode"

            try:
                # Get current chatmode
                current = self.chatmode_manager.get_chatmode(filename)

                # Prepare updated frontmatter
                frontmatter = current["frontmatter"].copy()
                if description is not None:
                    frontmatter["description"] = description
                if tools is not None:
                    # Parse comma-separated tools list
                    frontmatter["tools"] = [
                        tool.strip() for tool in tools.split(",") if tool.strip()
                    ]

                # Update the chatmode
                success = self.chatmode_manager.update_chatmode(
                    filename, frontmatter=frontmatter, content=content
                )

                if success:
                    return f"Successfully updated VS Code chatmode: {filename}"
                else:
                    return f"Failed to update VS Code chatmode: {filename}"

            except FileOperationError as e:
                return f"Error updating VS Code chatmode '{filename}': {str(e)}"
            except Exception as e:
                return (
                    f"Unexpected error updating VS Code chatmode '{filename}': {str(e)}"
                )

        @self.app.tool()
        def delete_chatmode(filename: str) -> str:
            """
            Delete a VS Code chatmode file.

            Args:
                filename: Name of the .chatmode.md file

            Returns:
                Success message or error
            """
            if self.read_only:
                return "Error: Server is running in read-only mode"

            try:
                success = self.chatmode_manager.delete_chatmode(filename)

                if success:
                    return f"Successfully deleted VS Code chatmode: {filename}"
                else:
                    return f"Failed to delete VS Code chatmode: {filename}"

            except FileOperationError as e:
                return f"Error deleting VS Code chatmode '{filename}': {str(e)}"
            except Exception as e:
                return (
                    f"Unexpected error deleting VS Code chatmode '{filename}': {str(e)}"
                )

        @self.app.tool()
        def update_chatmode_from_source(filename: str) -> str:
            """
            Update a VS Code chatmode file from its source URL.

            This fetches the latest version from the source_url in the frontmatter,
            while preserving any local tool customizations.

            Args:
                filename: Name of the .chatmode.md file

            Returns:
                Success message or error
            """
            if self.read_only:
                return "Error: Server is running in read-only mode"

            try:
                result = self.chatmode_manager.update_from_source(filename)

                return f"Successfully updated VS Code chatmode '{filename}' from source: {result['message']}"

            except FileOperationError as e:
                return f"Error updating VS Code chatmode '{filename}' from source: {str(e)}"
            except Exception as e:
                return f"Unexpected error updating VS Code chatmode '{filename}' from source: {str(e)}"

        # ========== INSTRUCTION TOOLS ==========

        @self.app.tool()
        def list_instructions() -> str:
            """
            List all VS Code .instructions.md files in the prompts directory.

            Returns:
                List of available instruction files
            """
            try:
                instructions = self.instruction_manager.list_instructions()

                if not instructions:
                    return "No VS Code instruction files found in the prompts directory"

                result = f"Found {len(instructions)} VS Code instruction(s):\\n\\n"
                for instruction in instructions:
                    result += f"📄 {instruction['name']}\\n"
                    result += f"   File: {instruction['filename']}\\n"
                    if instruction["description"]:
                        result += f"   Description: {instruction['description']}\\n"
                    result += f"   Size: {instruction['size']} bytes\\n"
                    if instruction["content_preview"]:
                        result += (
                            f"   Preview: {instruction['content_preview'][:100]}...\\n"
                        )
                    result += "\\n"

                return result

            except Exception as e:
                return f"Error listing VS Code instructions: {str(e)}"

        @self.app.tool()
        def get_instruction(filename: str) -> str:
            """
            Get content of a specific VS Code instruction file.

            Args:
                filename: Name of the .instructions.md file

            Returns:
                Raw instruction file content
            """
            try:
                # Ensure correct extension
                if not filename.endswith(INSTRUCTION_FILE_EXTENSION):
                    filename += INSTRUCTION_FILE_EXTENSION
                raw_content = self.instruction_manager.get_raw_instruction(filename)
                return raw_content

            except FileOperationError as e:
                return f"Error getting VS Code instruction '{filename}': {str(e)}"
            except Exception as e:
                return f"Unexpected error getting VS Code instruction '{filename}': {str(e)}"

        @self.app.tool()
        def create_instruction(filename: str, description: str, content: str) -> str:
            """
            Create a new VS Code instruction file.

            Args:
                filename: Name for the new .instructions.md file
                description: Description of the instruction
                content: Instruction content

            Returns:
                Success message or error
            """
            if self.read_only:
                return "Error: Server is running in read-only mode"

            try:
                # Ensure correct extension
                if not filename.endswith(INSTRUCTION_FILE_EXTENSION):
                    filename += INSTRUCTION_FILE_EXTENSION
                success = self.instruction_manager.create_instruction(
                    filename, description, content
                )

                if success:
                    return f"Successfully created VS Code instruction: {filename}"
                else:
                    return f"Failed to create VS Code instruction: {filename}"

            except FileOperationError as e:
                return f"Error creating VS Code instruction '{filename}': {str(e)}"
            except Exception as e:
                return f"Unexpected error creating VS Code instruction '{filename}': {str(e)}"

        @self.app.tool()
        def update_instruction(
            filename: str,
            description: Optional[str] = None,
            content: Optional[str] = None,
        ) -> str:
            """
            Update a VS Code instruction file.

            Args:
                filename: Name of the .instructions.md file
                description: New description (optional)
                content: New content (optional)

            Returns:
                Success message or error
            """
            if self.read_only:
                return "Error: Server is running in read-only mode"

            try:
                # Ensure correct extension
                if not filename.endswith(INSTRUCTION_FILE_EXTENSION):
                    filename += INSTRUCTION_FILE_EXTENSION
                # Build frontmatter updates
                frontmatter_updates = {}
                if description is not None:
                    frontmatter_updates["description"] = description

                success = self.instruction_manager.update_instruction(
                    filename,
                    frontmatter=frontmatter_updates if frontmatter_updates else None,
                    content=content,
                )

                if success:
                    return f"Successfully updated VS Code instruction: {filename}"
                else:
                    return f"Failed to update VS Code instruction: {filename}"

            except FileOperationError as e:
                return f"Error updating VS Code instruction '{filename}': {str(e)}"
            except Exception as e:
                return f"Unexpected error updating VS Code instruction '{filename}': {str(e)}"

        @self.app.tool()
        def delete_instruction(filename: str) -> str:
            """
            Delete a VS Code instruction file.

            Args:
                filename: Name of the .instructions.md file

            Returns:
                Success message or error
            """
            if self.read_only:
                return "Error: Server is running in read-only mode"

            try:
                # Ensure correct extension
                if not filename.endswith(INSTRUCTION_FILE_EXTENSION):
                    filename += INSTRUCTION_FILE_EXTENSION
                success = self.instruction_manager.delete_instruction(filename)

                if success:
                    return f"Successfully deleted VS Code instruction: {filename}"
                else:
                    return f"Failed to delete VS Code instruction: {filename}"

            except FileOperationError as e:
                return f"Error deleting VS Code instruction '{filename}': {str(e)}"
            except Exception as e:
                return f"Unexpected error deleting VS Code instruction '{filename}': {str(e)}"

        @self.app.tool()
        def get_prompts_directory() -> str:
            """
            Get the path to the VS Code prompts directory.

            Returns:
                Path to the prompts directory
            """
            try:
                prompts_dir = self.chatmode_manager.prompts_dir
                exists = prompts_dir.exists()

                result = f"VS Code Prompts Directory: {prompts_dir}\\n"
                result += f"Exists: {'Yes' if exists else 'No'}\\n"

                if exists:
                    chatmode_files = list(prompts_dir.glob("*.chatmode.md"))
                    instruction_files = list(
                        prompts_dir.glob(f"*{INSTRUCTION_FILE_EXTENSION}")
                    )

                    result += f"Chatmode files: {len(chatmode_files)}\\n"
                    result += f"Instruction files: {len(instruction_files)}\\n"

                    if chatmode_files:
                        result += "Chatmode files:\\n"
                        for file in sorted(chatmode_files):
                            result += f"  - {file.name}\\n"

                    if instruction_files:
                        result += "Instruction files:\\n"
                        for file in sorted(instruction_files):
                            result += f"  - {file.name}\\n"

                return result

            except Exception as e:
                return f"Error getting prompts directory info: {str(e)}"

        # ========== LIBRARY TOOLS ==========

        @self.app.tool()
        def browse_mode_library(
            category: Optional[str] = None, search: Optional[str] = None
        ) -> str:
            """
            Browse the Mode Manager MCP Library for available chatmodes and instructions.

            Args:
                category: Filter by category (optional, e.g., 'development', 'testing', 'python')
                search: Search term to filter by name, description, or tags (optional)

            Returns:
                Formatted list of available modes and instructions from the library
            """
            try:
                library_data = self.library_manager.browse_library(
                    category=category, search=search
                )

                result = (
                    f"📚 {library_data['library_name']} (v{library_data['version']})\\n"
                )
                result += f"📅 Last Updated: {library_data['last_updated']}\\n"
                result += f"📊 Total: {library_data['total_chatmodes']} chatmodes, {library_data['total_instructions']} instructions\\n"

                if (
                    library_data["filters_applied"]["category"]
                    or library_data["filters_applied"]["search"]
                ):
                    result += f"🔍 Filtered: {library_data['filtered_chatmodes']} chatmodes, {library_data['filtered_instructions']} instructions\\n"
                    filters = []
                    if library_data["filters_applied"]["category"]:
                        filters.append(
                            f"category: {library_data['filters_applied']['category']}"
                        )
                    if library_data["filters_applied"]["search"]:
                        filters.append(
                            f"search: {library_data['filters_applied']['search']}"
                        )
                    result += f"   Filters applied: {', '.join(filters)}\\n"

                result += "\\n"

                # Show chatmodes
                chatmodes = library_data["chatmodes"]
                if chatmodes:
                    result += f"🤖 **CHATMODES** ({len(chatmodes)} available):\\n\\n"
                    for cm in chatmodes:
                        result += (
                            f"**{cm['name']}** by {cm.get('author', 'Unknown')}\\n"
                        )
                        result += f"   📝 {cm.get('description', 'No description')}\\n"
                        result += f"   🏷️ Category: {cm.get('category', 'Unknown')}\\n"
                        if cm.get("tags"):
                            result += f"   🔖 Tags: {', '.join(cm['tags'])}\\n"
                        result += f"   📁 Install as: {cm.get('install_name', cm['name'] + '.chatmode.md')}\\n"
                        result += "\\n"
                else:
                    result += "🤖 No chatmodes found matching your criteria.\\n\\n"

                # Show instructions
                instructions = library_data["instructions"]
                if instructions:
                    result += (
                        f"📋 **INSTRUCTIONS** ({len(instructions)} available):\\n\\n"
                    )
                    for inst in instructions:
                        result += (
                            f"**{inst['name']}** by {inst.get('author', 'Unknown')}\\n"
                        )
                        result += (
                            f"   📝 {inst.get('description', 'No description')}\\n"
                        )
                        result += f"   🏷️ Category: {inst.get('category', 'Unknown')}\\n"
                        if inst.get("tags"):
                            result += f"   🔖 Tags: {', '.join(inst['tags'])}\\n"
                        result += f"   📁 Install as: {inst.get('install_name', inst['name'] + INSTRUCTION_FILE_EXTENSION)}\\n"
                        result += "\\n"
                else:
                    result += "📋 No instructions found matching your criteria.\\n\\n"

                # Show categories
                categories = library_data.get("categories", [])
                if categories:
                    result += "🗂️ **AVAILABLE CATEGORIES**:\\n"
                    for cat in categories:
                        result += f"   • {cat['name']} ({cat['id']}) - {cat.get('description', 'No description')}\\n"
                    result += "\\n"

                result += "💡 **Usage**: Use install_from_library('Name') to install any item.\\n"

                return result

            except FileOperationError as e:
                return f"Error browsing library: {str(e)}"
            except Exception as e:
                return f"Unexpected error browsing library: {str(e)}"

        @self.app.tool()
        def install_from_library(name: str, filename: Optional[str] = None) -> str:
            """
            Install a chatmode or instruction from the Mode Manager MCP Library.

            Args:
                name: Name of the chatmode or instruction to install (exact match required)
                filename: Custom filename for installation (optional)

            Returns:
                Installation result message
            """
            if self.read_only:
                return "Error: Server is running in read-only mode"

            try:
                result = self.library_manager.install_from_library(name, filename)

                if result["status"] == "success":
                    return (
                        f"✅ {result['message']}\\n\\n"
                        f"📁 Filename: {result['filename']}\\n"
                        f"🔗 Source: {result['source_url']}\\n"
                        f"📝 Type: {result['type'].title()}\\n\\n"
                        f"The {result['type']} is now available in VS Code!"
                    )
                else:
                    return f"❌ Installation failed: {result.get('message', 'Unknown error')}"

            except FileOperationError as e:
                return f"Error installing from library: {str(e)}"
            except Exception as e:
                return f"Unexpected error installing from library: {str(e)}"

        @self.app.tool()
        def refresh_library() -> str:
            """
            Refresh the Mode Manager MCP Library cache to get the latest available modes and instructions.

            Returns:
                Library refresh status and information
            """
            try:
                result = self.library_manager.refresh_library()

                if result["status"] == "success":
                    return (
                        f"✅ {result['message']}\\n\\n"
                        f"📚 Library: {result['library_name']} (v{result['version']})\\n"
                        f"📅 Last Updated: {result['last_updated']}\\n"
                        f"📊 Available: {result['total_chatmodes']} chatmodes, {result['total_instructions']} instructions\\n\\n"
                        f"Use browse_mode_library() to see the updated content."
                    )
                else:
                    return (
                        f"❌ Refresh failed: {result.get('message', 'Unknown error')}"
                    )

            except FileOperationError as e:
                return f"Error refreshing library: {str(e)}"
            except Exception as e:
                return f"Unexpected error refreshing library: {str(e)}"

    def run(self) -> None:
        """Run the MCP server."""
        self.app.run()


def create_server(library_url: Optional[str] = None) -> ModeManagerServer:
    """Create and return a Mode Manager MCP Server instance.

    Args:
        library_url: Custom URL for the Mode Manager MCP Library (optional)
    """
    return ModeManagerServer(library_url=library_url)
