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

# Update import to latest FastMCP (2.11.0)
from fastmcp import Context, FastMCP
from pydantic import BaseModel

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
        # FastMCP 2.11.0 initialization with recommended arguments
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
            on_duplicate_resources="warn",
            on_duplicate_prompts="replace",
            include_fastmcp_meta=True,  # Include FastMCP metadata for clients
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

        # Add built-in FastMCP middleware (2.11.0)
        from fastmcp.server.middleware.error_handling import ErrorHandlingMiddleware
        from fastmcp.server.middleware.logging import LoggingMiddleware
        from fastmcp.server.middleware.rate_limiting import RateLimitingMiddleware
        from fastmcp.server.middleware.timing import TimingMiddleware

        self.app.add_middleware(ErrorHandlingMiddleware())  # Handle errors first
        self.app.add_middleware(RateLimitingMiddleware(max_requests_per_second=50))
        self.app.add_middleware(TimingMiddleware())  # Time actual execution
        self.app.add_middleware(
            LoggingMiddleware(include_payloads=True, max_payload_length=1000)
        )

        # Register all tools
        self._register_tools()

        logger.info("Mode Manager MCP Server initialized")
        logger.info(f"Using library URL: {final_library_url}")
        if self.read_only:
            logger.info("Running in READ-ONLY mode")

    def _register_tools(self) -> None:
        @self.app.tool(
            tags={"public", "chatmode"},
            annotations={"idempotentHint": False, "readOnlyHint": False},
        )
        def delete_chatmode(filename: str) -> str:
            # Docstring removed
            if read_only:
                return "Error: Server is running in read-only mode"

            try:
                success = chatmode_manager.delete_chatmode(filename)

                if success:
                    return f"Successfully deleted VS Code chatmode: {filename}"
                else:
                    return f"Failed to delete VS Code chatmode: {filename}"

            except Exception as e:
                return f"Error deleting VS Code chatmode '{filename}': {str(e)}"

        @self.app.tool(
            tags={"public", "chatmode"},
            annotations={"idempotentHint": False, "readOnlyHint": False},
        )
        def update_chatmode_from_source(filename: str) -> str:
            # Function body placeholder
            return "Not implemented"

        @self.app.tool(
            tags={"public", "chatmode"},
            annotations={"idempotentHint": False, "readOnlyHint": False},
        )
        def create_chatmode(
            filename: str, description: str, content: str, tools: Optional[str] = None
        ) -> str:
            # Docstring removed
            if read_only:
                return "Error: Server is running in read-only mode"
            try:
                tools_list = tools.split(",") if tools else None
                success = chatmode_manager.create_chatmode(
                    filename, description, content, tools_list
                )
                if success:
                    return f"Successfully created VS Code chatmode: {filename}"
                else:
                    return f"Failed to create VS Code chatmode: {filename}"
            except Exception as e:
                return f"Error creating VS Code chatmode '{filename}': {str(e)}"

        @self.app.tool(
            tags={"public", "chatmode"},
            annotations={"idempotentHint": False, "readOnlyHint": False},
        )
        def update_chatmode(
            filename: str,
            description: Optional[str] = None,
            content: Optional[str] = None,
            tools: Optional[str] = None,
        ) -> str:
            # Docstring removed
            if read_only:
                return "Error: Server is running in read-only mode"
            try:
                frontmatter = {}
                if description is not None:
                    frontmatter["description"] = description
                if isinstance(tools, str):
                    frontmatter["tools"] = tools
                success = chatmode_manager.update_chatmode(
                    filename, frontmatter if frontmatter else None, content
                )
                if success:
                    return f"Successfully updated VS Code chatmode: {filename}"
                else:
                    return f"Failed to update VS Code chatmode: {filename}"

            except Exception as e:
                return f"Error updating VS Code chatmode '{filename}': {str(e)}"

        @self.app.tool(
            tags={"public", "chatmode"},
            annotations={"idempotentHint": True, "readOnlyHint": True},
        )
        def list_chatmodes() -> str:
            # Docstring removed
            try:
                chatmodes = chatmode_manager.list_chatmodes()
                if not chatmodes:
                    return "No VS Code chatmode files found in the prompts directory"
                result = f"Found {len(chatmodes)} VS Code chatmode(s):\n\n"
                for cm in chatmodes:
                    result += f"🤖 {cm['name']}\n"
                    result += f"   File: {cm['filename']}\n"
                    if cm["description"]:
                        result += f"   Description: {cm['description']}\n"
                    result += f"   Size: {cm['size']} bytes\n"
                    if cm["content_preview"]:
                        result += f"   Preview: {cm['content_preview'][:100]}...\n"
                    result += "\n"
                return result
            except Exception as e:
                return f"Error listing VS Code chatmodes: {str(e)}"

        @self.app.tool(
            tags={"public", "chatmode"},
            annotations={"idempotentHint": True, "readOnlyHint": True},
        )
        def get_chatmode(filename: str) -> str:
            # Docstring removed
            try:
                if not filename.endswith(".chatmode.md"):
                    filename += ".chatmode.md"
                raw_content = chatmode_manager.get_raw_chatmode(filename)
                return raw_content
            except Exception as e:
                return f"Error getting VS Code chatmode '{filename}': {str(e)}"

        @self.app.tool(
            tags={"public", "instruction"},
            annotations={"idempotentHint": False, "readOnlyHint": False},
        )
        def create_instruction(filename: str, description: str, content: str) -> str:
            # Docstring removed
            if read_only:
                return "Error: Server is running in read-only mode"
            try:
                success = instruction_manager.create_instruction(
                    filename, description, content
                )
                if success:
                    return f"Successfully created VS Code instruction: {filename}"
                else:
                    return f"Failed to create VS Code instruction: {filename}"
            except Exception as e:
                return f"Error creating VS Code instruction '{filename}': {str(e)}"

        @self.app.tool(
            tags={"public", "instruction"},
            annotations={"idempotentHint": False, "readOnlyHint": False},
        )
        def update_instruction(
            filename: str,
            description: Optional[str] = None,
            content: Optional[str] = None,
        ) -> str:
            # Docstring removed
            if read_only:
                return "Error: Server is running in read-only mode"
            try:
                success = instruction_manager.update_instruction(
                    filename, content=content
                )
                if success:
                    return f"Successfully updated VS Code instruction: {filename}"
                else:
                    return f"Failed to update VS Code instruction: {filename}"
            except Exception as e:
                return f"Error updating VS Code instruction '{filename}': {str(e)}"

        @self.app.tool(
            tags={"public", "instruction"},
            annotations={"idempotentHint": False, "readOnlyHint": False},
        )
        def delete_instruction(filename: str) -> str:
            # Docstring removed
            if read_only:
                return "Error: Server is running in read-only mode"
            try:
                success = instruction_manager.delete_instruction(filename)
                if success:
                    return f"Successfully deleted VS Code instruction: {filename}"
                else:
                    return f"Failed to delete VS Code instruction: {filename}"
            except Exception as e:
                return f"Error deleting VS Code instruction '{filename}': {str(e)}"

        @self.app.tool(
            tags={"public", "library"},
            annotations={"idempotentHint": True, "readOnlyHint": True},
        )
        def refresh_library() -> str:
            try:
                result = library_manager.refresh_library()
                if result["status"] == "success":
                    return (
                        f"✅ {result['message']}\n\n"
                        f"📚 Library: {result['library_name']} (v{result['version']})\n"
                        f"📅 Last Updated: {result['last_updated']}\n"
                        f"📊 Available: {result['total_chatmodes']} chatmodes, {result['total_instructions']} instructions\n\n"
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

        @self.app.tool(
            tags={"public", "prompts"},
            annotations={"idempotentHint": True, "readOnlyHint": True},
        )
        def get_prompts_directory() -> str:
            try:
                return str(instruction_manager.prompts_dir)
            except Exception as e:
                return f"Error getting prompts directory: {str(e)}"

        @self.app.tool(
            tags={"public", "instruction"},
            annotations={"idempotentHint": True, "readOnlyHint": True},
        )
        def list_instructions() -> str:
            try:
                instructions = instruction_manager.list_instructions()

                if not instructions:
                    return "No VS Code instruction files found in the prompts directory"

                result = f"Found {len(instructions)} VS Code instruction(s):\n\n"
                for instruction in instructions:
                    result += f"📄 {instruction['name']}\n"
                    result += f"   File: {instruction['filename']}\n"
                    if instruction["description"]:
                        result += f"   Description: {instruction['description']}\n"
                    result += f"   Size: {instruction['size']} bytes\n"
                    if instruction["content_preview"]:
                        result += (
                            f"   Preview: {instruction['content_preview'][:100]}...\n"
                        )
                    result += "\n"

                return result

            except Exception as e:
                return f"Error listing VS Code instructions: {str(e)}"

        @self.app.tool(
            tags={"public", "instruction"},
            annotations={"idempotentHint": True, "readOnlyHint": True},
        )
        def get_instruction(filename: str) -> str:
            try:
                # Ensure correct extension
                if not filename.endswith(INSTRUCTION_FILE_EXTENSION):
                    filename += INSTRUCTION_FILE_EXTENSION
                raw_content = instruction_manager.get_raw_instruction(filename)
                return raw_content
            except Exception as e:
                return f"Error getting VS Code instruction '{filename}': {str(e)}"

        class RememberOutput(BaseModel):
            status: str
            message: str
            memory_path: str

        instruction_manager = self.instruction_manager
        chatmode_manager = self.chatmode_manager
        library_manager = self.library_manager
        read_only = self.read_only

        @self.app.tool(
            tags={"public", "memory"},
            annotations={"idempotentHint": True, "readOnlyHint": False},
        )
        async def remember(memory_item: Optional[str] = None) -> str:
            if read_only:
                return "Error: Server is running in read-only mode"
            if memory_item is None:
                return "Error: No memory item provided."
            try:
                import datetime

                memory_filename = f"memory{INSTRUCTION_FILE_EXTENSION}"
                memory_path = instruction_manager.prompts_dir / memory_filename
                if not memory_path.exists():
                    initial_content = "# Personal AI Memory\nThis file contains information that I should remember about you and your preferences for future conversations.\n## Memories\n"
                    success = instruction_manager.create_instruction(
                        memory_filename,
                        "Personal AI memory for conversations and preferences",
                        initial_content,
                    )
                    if not success:
                        return f"Error: Failed to create memory file at {memory_path}"
                    logger.info("Created new memory file for user")
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                new_memory_entry = f"- **{timestamp}**: {memory_item}\n"
                # Use the new append_to_section method to safely append
                success = instruction_manager.append_to_section(
                    memory_filename, section_header="## Memories", new_entry=new_memory_entry
                )
                if success:
                    return f"✅ Remembered: {memory_item}\n\n💡 This memory will be available to AI assistants when the memory instruction is active in VS Code."
                else:
                    return f"Error: Failed to update memory file at {memory_path}"
            except Exception as e:
                return f"Error: Exception occurred: {str(e)}"

        @self.app.tool(
            tags={"public", "library"},
            annotations={"idempotentHint": True, "readOnlyHint": True},
        )
        def browse_mode_library(
            category: Optional[str] = None, search: Optional[str] = None
        ) -> str:
            try:
                library_data = library_manager.browse_library(
                    category=category, search=search
                )
                result = (
                    f"📚 {library_data['library_name']} (v{library_data['version']})\n"
                )
                result += f"📅 Last Updated: {library_data['last_updated']}\n"
                result += f"📊 Total: {library_data['total_chatmodes']} chatmodes, {library_data['total_instructions']} instructions\n"
                if (
                    library_data["filters_applied"]["category"]
                    or library_data["filters_applied"]["search"]
                ):
                    result += f"🔍 Filtered: {library_data['filtered_chatmodes']} chatmodes, {library_data['filtered_instructions']} instructions\n"
                    filters = []
                    if library_data["filters_applied"]["category"]:
                        filters.append(
                            f"category: {library_data['filters_applied']['category']}"
                        )
                    if library_data["filters_applied"]["search"]:
                        filters.append(
                            f"search: {library_data['filters_applied']['search']}"
                        )
                    result += f"   Filters applied: {', '.join(filters)}\n"
                result += "\n"
                chatmodes = library_data["chatmodes"]
                if chatmodes:
                    result += f"🤖 **CHATMODES** ({len(chatmodes)} available):\n\n"
                    for cm in chatmodes:
                        result += f"**{cm['name']}** by {cm.get('author', 'Unknown')}\n"
                        result += f"   📝 {cm.get('description', 'No description')}\n"
                        result += f"   🏷️ Category: {cm.get('category', 'Unknown')}\n"
                        if cm.get("tags"):
                            result += f"   🔖 Tags: {', '.join(cm['tags'])}\n"
                        result += f"   📁 Install as: {cm.get('install_name', cm['name'] + '.chatmode.md')}\n"
                        result += "\n"
                else:
                    result += "🤖 No chatmodes found matching your criteria.\n\n"
                instructions = library_data["instructions"]
                if instructions:
                    result += (
                        f"📋 **INSTRUCTIONS** ({len(instructions)} available):\n\n"
                    )
                    for inst in instructions:
                        result += (
                            f"**{inst['name']}** by {inst.get('author', 'Unknown')}\n"
                        )
                        result += f"   📝 {inst.get('description', 'No description')}\n"
                        result += f"   🏷️ Category: {inst.get('category', 'Unknown')}\n"
                        if inst.get("tags"):
                            result += f"   🔖 Tags: {', '.join(inst['tags'])}\n"
                        result += f"   📁 Install as: {inst.get('install_name', inst['name'] + INSTRUCTION_FILE_EXTENSION)}\n"
                        result += "\n"
                else:
                    result += "📋 No instructions found matching your criteria.\n\n"
                categories = library_data.get("categories", [])
                if categories:
                    result += "🗂️ **AVAILABLE CATEGORIES**:\n"
                    for cat in categories:
                        result += f"   • {cat['name']} ({cat['id']}) - {cat.get('description', 'No description')}\n"
                    result += "\n"
                result += "💡 **Usage**: Use install_from_library('Name') to install any item.\n"
                return result
            except FileOperationError as e:
                return f"Error browsing library: {str(e)}"
            except Exception as e:
                return f"Unexpected error browsing library: {str(e)}"

        @self.app.tool(
            tags={"public", "library"},
            annotations={"idempotentHint": False, "readOnlyHint": False},
        )
        def install_from_library(name: str, filename: Optional[str] = None) -> str:
            if read_only:
                return "Error: Server is running in read-only mode"
            try:
                result = library_manager.install_from_library(name, filename)
                if result["status"] == "success":
                    return (
                        f"✅ {result['message']}\n\n"
                        f"📁 Filename: {result['filename']}\n"
                        f"🔗 Source: {result['source_url']}\n"
                        f"📝 Type: {result['type'].title()}\n\n"
                        f"The {result['type']} is now available in VS Code!"
                    )
                else:
                    return f"❌ Installation failed: {result.get('message', 'Unknown error')}"
            except FileOperationError as e:
                return f"Error installing from library: {str(e)}"
            except Exception as e:
                return f"Unexpected error installing from library: {str(e)}"

    def run(self) -> None:
        self.app.run()


def create_server(library_url: Optional[str] = None) -> ModeManagerServer:
    return ModeManagerServer(library_url=library_url)
