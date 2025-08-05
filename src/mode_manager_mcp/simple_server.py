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
from typing import Annotated, Optional

from fastmcp import Context, FastMCP
from fastmcp.prompts.prompt import Message
from fastmcp.server.middleware.error_handling import ErrorHandlingMiddleware
from fastmcp.server.middleware.logging import LoggingMiddleware
from fastmcp.server.middleware.rate_limiting import RateLimitingMiddleware
from fastmcp.server.middleware.timing import TimingMiddleware
from pydantic import BaseModel, Field

from .chatmode_manager import ChatModeManager
from .instruction_manager import INSTRUCTION_FILE_EXTENSION, InstructionManager
from .library_manager import LibraryManager
from .simple_file_ops import FileOperationError

logger = logging.getLogger(__name__)


class ModeManagerServer:
    """
    Mode Manager MCP Server.

    Provides tools for managing VS Code .chatmode.md and .instructions.md files.
    """

    def __init__(self, library_url: Optional[str] = None, prompts_dir: Optional[str] = None):
        """Initialize the server.

        Args:
            library_url: Custom URL for the Mode Manager MCP Library (optional)
            prompts_dir: Custom prompts directory for all managers (optional)
        """
        # FastMCP 2.11.0 initialization with recommended arguments
        self.app = FastMCP(
            name="Mode Manager MCP",
            instructions="""
            Persistent Copilot Memory for VS Code (2025+).

            GitHub Repository: https://github.com/NiclasOlofsson/mode-manager-mcp

            Game-Changer for 2025:
            - Copilot now loads instructions with every chat message, not just at session start.
            - Your memories and preferences are ALWAYS active in every conversation, across sessions, topics, and projects.

            Main Feature:
            - Store your work context, coding preferences, and workflow details using the remember(memory_item) tool.

            How It Works:
            - Auto-setup: Creates memory.instructions.md in your VS Code prompts directory on first use.
            - Smart storage: Each memory is timestamped and organized for easy retrieval.
            - Always loaded: VS Code includes your memories in every chat request.

            Additional Capabilities:
            - Manage and organize .chatmode.md and .instructions.md files.
            - Browse and install curated chatmodes and instructions from the Mode Manager MCP Library.
            - Refresh files from source while keeping your customizations.

            Usage Example:
            - Ask Copilot: "Remember that I prefer detailed docstrings and use pytest for testing"
            - Copilot will remember this across all future conversations.
            """,
            on_duplicate_resources="warn",
            on_duplicate_prompts="replace",
            include_fastmcp_meta=True,  # Include FastMCP metadata for clients
        )
        self.chatmode_manager = ChatModeManager(prompts_dir=prompts_dir)
        self.instruction_manager = InstructionManager(prompts_dir=prompts_dir)

        # Allow library URL to be configured via parameter, environment variable, or use default
        final_library_url = library_url or os.getenv("MCP_LIBRARY_URL") or "https://raw.githubusercontent.com/NiclasOlofsson/node-manager-mcp/refs/heads/main/library/memory-mode-library.json"
        self.library_manager = LibraryManager(library_url=final_library_url, prompts_dir=prompts_dir)

        self.read_only = os.getenv("MCP_CHATMODE_READ_ONLY", "false").lower() == "true"

        # Add built-in FastMCP middleware (2.11.0)
        self.app.add_middleware(ErrorHandlingMiddleware())  # Handle errors first
        self.app.add_middleware(RateLimitingMiddleware(max_requests_per_second=50))
        self.app.add_middleware(TimingMiddleware())  # Time actual execution
        self.app.add_middleware(LoggingMiddleware(include_payloads=True, max_payload_length=1000))

        # Register all tools
        self._register_tools()

        logger.info("Mode Manager MCP Server initialized")
        logger.info(f"Using library URL: {final_library_url}")
        if self.read_only:
            logger.info("Running in READ-ONLY mode")

    def _register_tools(self) -> None:
        # ===== INSTRUCTIONS GROUP (CLRUD ORDER) =====

        @self.app.tool(
            name="create_instruction",
            description="Create a new VS Code .instructions.md file with the specified description and content.",
            tags={"public", "instruction"},
            annotations={
                "idempotentHint": False,
                "readOnlyHint": False,
                "title": "Create Instruction",
                "parameters": {
                    "instruction_name": "The name for the new instruction. If .instructions.md extension is not provided, it will be added automatically.",
                    "description": "A brief description of what this instruction does. This will be stored in the frontmatter.",
                    "content": "The main content/instructions in markdown format.",
                },
                "returns": "Returns a success message if the instruction was created, or an error message if the operation failed.",
            },
            meta={
                "category": "instruction",
                "version": "1.0",
            },
        )
        def create_instruction(
            instruction_name: Annotated[
                str,
                Field(description="The name for the new instruction (with or without extension)"),
            ],
            description: Annotated[
                str,
                Field(description="A brief description of what this instruction does"),
            ],
            content: Annotated[
                str,
                Field(description="The main content/instructions in markdown format"),
            ],
        ) -> str:
            """Create a new VS Code .instructions.md file with the specified description and content."""
            if read_only:
                return "Error: Server is running in read-only mode"
            try:
                success = instruction_manager.create_instruction(instruction_name, description, content)
                if success:
                    return f"Successfully created VS Code instruction: {instruction_name}"
                else:
                    return f"Failed to create VS Code instruction: {instruction_name}"
            except Exception as e:
                return f"Error creating VS Code instruction '{instruction_name}': {str(e)}"

        @self.app.tool(
            name="list_instructions",
            description="List all VS Code .instructions.md files in the prompts directory.",
            tags={"public", "instruction"},
            annotations={
                "idempotentHint": True,
                "readOnlyHint": True,
                "title": "List Instructions",
                "returns": "Returns a formatted list of all instruction files with their names, descriptions, sizes, and content previews. If no instructions are found, returns an informational message.",
            },
            meta={
                "category": "instruction",
                "version": "1.0",
            },
        )
        def list_instructions() -> str:
            """List all VS Code .instructions.md files in the prompts directory."""
            try:
                instructions = instruction_manager.list_instructions()
                if not instructions:
                    return "No VS Code instruction files found in the prompts directory"
                result = f"Found {len(instructions)} VS Code instruction(s):\n\n"
                for instruction in instructions:
                    result += f"Name: {instruction['name']}\n"
                    result += f"   File: {instruction['filename']}\n"
                    if instruction["description"]:
                        result += f"   Description: {instruction['description']}\n"
                    result += f"   Size: {instruction['size']} bytes\n"
                    if instruction["content_preview"]:
                        result += f"   Preview: {instruction['content_preview'][:100]}...\n"
                    result += "\n"
                return result
            except Exception as e:
                return f"Error listing VS Code instructions: {str(e)}"

        @self.app.tool(
            name="get_instruction",
            description="Get the raw content of a VS Code .instructions.md file.",
            tags={"public", "instruction"},
            annotations={
                "idempotentHint": True,
                "readOnlyHint": True,
                "title": "Get Instruction",
                "parameters": {
                    "instruction_name": "The name of the instruction (without extension). If a full filename is provided, it will be used as-is. Otherwise, .instructions.md will be appended automatically. This tool is flexible: you can provide just the name (e.g. <instruction_name>) or the full filename (e.g. <instruction_name>.instructions.md). If the extension is missing, it will be added automatically."
                },
                "returns": "Returns the raw markdown content of the specified instruction file, or an error message if not found. Display recommendation: If the file is longer than 40 lines, show the first 10 lines, then '........', then the last 10 lines.",
            },
            meta={
                "category": "instruction",
                "version": "1.0",
            },
        )
        def get_instruction(
            instruction_name: Annotated[str, Field(description="Name of the instruction (without extension)")],
        ) -> str:
            """Get the raw content of a VS Code .instructions.md file."""
            try:
                # Ensure correct extension
                if not instruction_name.endswith(INSTRUCTION_FILE_EXTENSION):
                    instruction_name += INSTRUCTION_FILE_EXTENSION
                raw_content = instruction_manager.get_raw_instruction(instruction_name)
                return raw_content
            except Exception as e:
                return f"Error getting VS Code instruction '{instruction_name}': {str(e)}"

        @self.app.tool(
            name="update_instruction",
            description="Update an existing VS Code .instructions.md file with new description or content.",
            tags={"public", "instruction"},
            annotations={
                "idempotentHint": False,
                "readOnlyHint": False,
                "title": "Update Instruction",
                "parameters": {
                    "instruction_name": "The name of the instruction to update. If .instructions.md extension is not provided, it will be added automatically.",
                    "description": "Optional new description for the instruction. If not provided, the existing description will be kept.",
                    "content": "Optional new content for the instruction. If not provided, the existing content will be kept.",
                },
                "returns": "Returns a success message if the instruction was updated, or an error message if the operation failed.",
            },
            meta={
                "category": "instruction",
                "version": "1.0",
            },
        )
        def update_instruction(
            instruction_name: Annotated[
                str,
                Field(description="The name of the instruction to update (with or without extension)"),
            ],
            description: Annotated[
                Optional[str],
                Field(description="Optional new description for the instruction"),
            ] = None,
            content: Annotated[
                Optional[str],
                Field(description="Optional new content for the instruction"),
            ] = None,
        ) -> str:
            """Update an existing VS Code .instructions.md file with new description or content."""
            if read_only:
                return "Error: Server is running in read-only mode"
            try:
                success = instruction_manager.update_instruction(instruction_name, content=content)
                if success:
                    return f"Successfully updated VS Code instruction: {instruction_name}"
                else:
                    return f"Failed to update VS Code instruction: {instruction_name}"
            except Exception as e:
                return f"Error updating VS Code instruction '{instruction_name}': {str(e)}"

        @self.app.tool(
            name="delete_instruction",
            description="Delete a VS Code .instructions.md file from the prompts directory.",
            tags={"public", "instruction"},
            annotations={
                "idempotentHint": False,
                "readOnlyHint": False,
                "title": "Delete Instruction",
                "parameters": {
                    "instruction_name": "The name of the instruction to delete. If a full filename is provided, it will be used as-is. Otherwise, .instructions.md will be appended automatically. You can provide just the name (e.g. my-instruction) or the full filename (e.g. my-instruction.instructions.md)."
                },
                "returns": "Returns a success message if the instruction was deleted, or an error message if the operation failed or the file was not found.",
            },
            meta={
                "category": "instruction",
                "version": "1.0",
            },
        )
        def delete_instruction(
            instruction_name: Annotated[
                str,
                Field(description="The name of the instruction to delete (with or without extension)"),
            ],
        ) -> str:
            """Delete a VS Code .instructions.md file from the prompts directory."""
            if read_only:
                return "Error: Server is running in read-only mode"
            try:
                success = instruction_manager.delete_instruction(instruction_name)
                if success:
                    return f"Successfully deleted VS Code instruction: {instruction_name}"
                else:
                    return f"Failed to delete VS Code instruction: {instruction_name}"
            except Exception as e:
                return f"Error deleting VS Code instruction '{instruction_name}': {str(e)}"

        # ===== CHATMODE GROUP (CLRUD ORDER + RELATED) =====

        @self.app.tool(
            name="create_chatmode",
            description="Create a new VS Code .chatmode.md file with the specified description, content, and tools.",
            tags={"public", "chatmode"},
            annotations={
                "idempotentHint": False,
                "readOnlyHint": False,
                "title": "Create Chatmode",
                "parameters": {
                    "filename": "The filename for the new chatmode. If .chatmode.md extension is not provided, it will be added automatically.",
                    "description": "A brief description of what this chatmode does. This will be stored in the frontmatter.",
                    "content": "The main content/instructions for the chatmode in markdown format.",
                    "tools": "Optional comma-separated list of tool names that this chatmode should have access to.",
                },
                "returns": "Returns a success message if the chatmode was created, or an error message if the operation failed.",
            },
            meta={
                "category": "chatmode",
                "version": "1.0",
            },
        )
        def create_chatmode(
            filename: Annotated[
                str,
                Field(description="The filename for the new chatmode (with or without extension)"),
            ],
            description: Annotated[str, Field(description="A brief description of what this chatmode does")],
            content: Annotated[
                str,
                Field(description="The main content/instructions for the chatmode in markdown format"),
            ],
            tools: Annotated[
                Optional[str],
                Field(description="Optional comma-separated list of tool names"),
            ] = None,
        ) -> str:
            """Create a new VS Code .chatmode.md file with the specified description, content, and tools."""
            if read_only:
                return "Error: Server is running in read-only mode"
            try:
                tools_list = tools.split(",") if tools else None
                success = chatmode_manager.create_chatmode(filename, description, content, tools_list)
                if success:
                    return f"Successfully created VS Code chatmode: {filename}"
                else:
                    return f"Failed to create VS Code chatmode: {filename}"
            except Exception as e:
                return f"Error creating VS Code chatmode '{filename}': {str(e)}"

        @self.app.tool(
            name="list_chatmodes",
            description="List all VS Code .chatmode.md files in the prompts directory.",
            tags={"public", "chatmode"},
            annotations={
                "idempotentHint": True,
                "readOnlyHint": True,
                "title": "List Chatmodes",
                "returns": "Returns a formatted list of all chatmode files with their names, descriptions, sizes, and content previews. If no chatmodes are found, returns an informational message.",
            },
            meta={
                "category": "chatmode",
                "version": "1.0",
            },
        )
        def list_chatmodes() -> str:
            """List all VS Code .chatmode.md files in the prompts directory."""
            try:
                chatmodes = chatmode_manager.list_chatmodes()
                if not chatmodes:
                    return "No VS Code chatmode files found in the prompts directory"
                result = f"Found {len(chatmodes)} VS Code chatmode(s):\n\n"
                for cm in chatmodes:
                    result += f"Name: {cm['name']}\n"
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
            name="get_chatmode",
            description="Get the raw content of a VS Code .chatmode.md file.",
            tags={"public", "chatmode"},
            annotations={
                "idempotentHint": True,
                "readOnlyHint": True,
                "title": "Get Chatmode",
                "parameters": {
                    "filename": "The filename of the chatmode to retrieve. If a full filename is provided, it will be used as-is. Otherwise, .chatmode.md will be appended automatically. You can provide just the name (e.g. my-chatmode) or the full filename (e.g. my-chatmode.chatmode.md)."
                },
                "returns": "Returns the raw markdown content of the specified chatmode file, or an error message if not found. Display recommendation: If the file is longer than 40 lines, show the first 10 lines, then '........', then the last 10 lines.",
            },
            meta={
                "category": "chatmode",
                "version": "1.0",
            },
        )
        def get_chatmode(
            filename: Annotated[
                str,
                Field(description="The filename of the chatmode to retrieve (with or without extension)"),
            ],
        ) -> str:
            """Get the raw content of a VS Code .chatmode.md file."""
            try:
                if not filename.endswith(".chatmode.md"):
                    filename += ".chatmode.md"
                raw_content = chatmode_manager.get_raw_chatmode(filename)
                return raw_content
            except Exception as e:
                return f"Error getting VS Code chatmode '{filename}': {str(e)}"

        @self.app.tool(
            name="update_chatmode",
            description="Update an existing VS Code .chatmode.md file with new description, content, or tools.",
            tags={"public", "chatmode"},
            annotations={
                "idempotentHint": False,
                "readOnlyHint": False,
                "title": "Update Chatmode",
                "parameters": {
                    "filename": "The filename of the chatmode to update. If .chatmode.md extension is not provided, it will be added automatically.",
                    "description": "Optional new description for the chatmode. If not provided, the existing description will be kept.",
                    "content": "Optional new content for the chatmode. If not provided, the existing content will be kept.",
                    "tools": "Optional new comma-separated list of tool names. If not provided, the existing tools will be kept.",
                },
                "returns": "Returns a success message if the chatmode was updated, or an error message if the operation failed.",
            },
            meta={
                "category": "chatmode",
                "version": "1.0",
            },
        )
        def update_chatmode(
            filename: Annotated[
                str,
                Field(description="The filename of the chatmode to update (with or without extension)"),
            ],
            description: Annotated[
                Optional[str],
                Field(description="Optional new description for the chatmode"),
            ] = None,
            content: Annotated[
                Optional[str],
                Field(description="Optional new content for the chatmode"),
            ] = None,
            tools: Annotated[
                Optional[str],
                Field(description="Optional new comma-separated list of tool names"),
            ] = None,
        ) -> str:
            """Update an existing VS Code .chatmode.md file with new description, content, or tools."""
            if read_only:
                return "Error: Server is running in read-only mode"
            try:
                frontmatter = {}
                if description is not None:
                    frontmatter["description"] = description
                if isinstance(tools, str):
                    frontmatter["tools"] = tools
                success = chatmode_manager.update_chatmode(filename, frontmatter if frontmatter else None, content)
                if success:
                    return f"Successfully updated VS Code chatmode: {filename}"
                else:
                    return f"Failed to update VS Code chatmode: {filename}"
            except Exception as e:
                return f"Error updating VS Code chatmode '{filename}': {str(e)}"

        @self.app.tool(
            name="delete_chatmode",
            description="Delete a VS Code .chatmode.md file from the prompts directory.",
            tags={"public", "chatmode"},
            annotations={
                "idempotentHint": False,
                "readOnlyHint": False,
                "title": "Delete Chatmode",
                "parameters": {
                    "filename": "The filename of the chatmode to delete. If a full filename is provided, it will be used as-is. Otherwise, .chatmode.md will be appended automatically. You can provide just the name (e.g. my-chatmode) or the full filename (e.g. my-chatmode.chatmode.md)."
                },
                "returns": "Returns a success message if the chatmode was deleted, or an error message if the operation failed or the file was not found.",
            },
            meta={
                "category": "chatmode",
                "version": "1.0",
            },
        )
        def delete_chatmode(
            filename: Annotated[
                str,
                Field(description="The filename of the chatmode to delete (with or without extension)"),
            ],
        ) -> str:
            """Delete a VS Code .chatmode.md file from the prompts directory."""
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
            name="update_chatmode_from_source",
            description="Update a .chatmode.md file from its source definition.",
            tags={"public", "chatmode"},
            annotations={
                "idempotentHint": False,
                "readOnlyHint": False,
                "title": "Update Chatmode from Source",
                "parameters": {"filename": "The filename of the chatmode to update from its source. If .chatmode.md extension is not provided, it will be added automatically."},
                "returns": "Returns a success message if the chatmode was updated from source, or an error message. Note: This feature is currently not implemented.",
            },
            meta={
                "category": "chatmode",
                "version": "1.0",
            },
        )
        def update_chatmode_from_source(
            filename: Annotated[
                str,
                Field(description="The filename of the chatmode to update from source (with or without extension)"),
            ],
        ) -> str:
            """Update a .chatmode.md file from its source definition."""
            return "Not implemented"

        # ===== LIBRARY GROUP =====

        @self.app.tool(
            name="refresh_library",
            description="Refresh the Mode Manager MCP Library from its source URL.",
            tags={"public", "library"},
            annotations={
                "idempotentHint": True,
                "readOnlyHint": True,
                "title": "Refresh Library",
                "returns": "Returns information about the library refresh operation, including library name, version, last updated date, and counts of available chatmodes and instructions. Also provides usage instructions.",
            },
            meta={"category": "library", "version": "1.0", "author": "Oatly Data Team"},
        )
        def refresh_library() -> str:
            """Refresh the Mode Manager MCP Library from its source URL."""
            try:
                result = library_manager.refresh_library()
                if result["status"] == "success":
                    return (
                        f"{result['message']}\n\n"
                        f"Library: {result['library_name']} (v{result['version']})\n"
                        f"Last Updated: {result['last_updated']}\n"
                        f"Available: {result['total_chatmodes']} chatmodes, {result['total_instructions']} instructions\n\n"
                        f"Use browse_mode_library() to see the updated content."
                    )
                else:
                    return f"Refresh failed: {result.get('message', 'Unknown error')}"
            except FileOperationError as e:
                return f"Error refreshing library: {str(e)}"
            except Exception as e:
                return f"Unexpected error refreshing library: {str(e)}"

        @self.app.tool(
            name="browse_mode_library",
            description="Browse the Mode Manager MCP Library and filter by category or search term.",
            tags={"public", "library"},
            annotations={
                "idempotentHint": True,
                "readOnlyHint": True,
                "title": "Browse Mode Library",
                "parameters": {
                    "category": "Optional category filter to show only items from a specific category. Use list without filter to see available categories.",
                    "search": "Optional search term to filter items by name, description, or tags.",
                },
                "returns": "Returns a formatted list of available chatmodes and instructions from the library, with details like name, author, description, category, and installation name. Also shows available categories and usage instructions.",
            },
            meta={"category": "library", "version": "1.0", "author": "Oatly Data Team"},
        )
        def browse_mode_library(
            category: Annotated[Optional[str], Field(description="Optional category filter")] = None,
            search: Annotated[Optional[str], Field(description="Optional search term")] = None,
        ) -> str:
            """Browse the Mode Manager MCP Library and filter by category or search term."""
            try:
                library_data = library_manager.browse_library(category=category, search=search)
                result = f"Library: {library_data['library_name']} (v{library_data['version']})\n"
                result += f"Last Updated: {library_data['last_updated']}\n"
                result += f"Total: {library_data['total_chatmodes']} chatmodes, {library_data['total_instructions']} instructions\n"
                if library_data["filters_applied"]["category"] or library_data["filters_applied"]["search"]:
                    result += f"Filtered: {library_data['filtered_chatmodes']} chatmodes, {library_data['filtered_instructions']} instructions\n"
                    filters = []
                    if library_data["filters_applied"]["category"]:
                        filters.append(f"category: {library_data['filters_applied']['category']}")
                    if library_data["filters_applied"]["search"]:
                        filters.append(f"search: {library_data['filters_applied']['search']}")
                    result += f"   Filters applied: {', '.join(filters)}\n"
                result += "\n"
                chatmodes = library_data["chatmodes"]
                if chatmodes:
                    result += f"CHATMODES ({len(chatmodes)} available):\n\n"
                    for cm in chatmodes:
                        result += f"{cm['name']} by {cm.get('author', 'Unknown')}\n"
                        result += f"   Description: {cm.get('description', 'No description')}\n"
                        result += f"   Category: {cm.get('category', 'Unknown')}\n"
                        if cm.get("tags"):
                            result += f"   Tags: {', '.join(cm['tags'])}\n"
                        result += f"   Install as: {cm.get('install_name', cm['name'] + '.chatmode.md')}\n"
                        result += "\n"
                else:
                    result += "No chatmodes found matching your criteria.\n\n"
                instructions = library_data["instructions"]
                if instructions:
                    result += f"INSTRUCTIONS ({len(instructions)} available):\n\n"
                    for inst in instructions:
                        result += f"{inst['name']} by {inst.get('author', 'Unknown')}\n"
                        result += f"   Description: {inst.get('description', 'No description')}\n"
                        result += f"   Category: {inst.get('category', 'Unknown')}\n"
                        if inst.get("tags"):
                            result += f"   Tags: {', '.join(inst['tags'])}\n"
                        result += f"   Install as: {inst.get('install_name', inst['name'] + INSTRUCTION_FILE_EXTENSION)}\n"
                        result += "\n"
                else:
                    result += "No instructions found matching your criteria.\n\n"
                categories = library_data.get("categories", [])
                if categories:
                    result += "AVAILABLE CATEGORIES:\n"
                    for cat in categories:
                        result += f"   • {cat['name']} ({cat['id']}) - {cat.get('description', 'No description')}\n"
                    result += "\n"
                result += "Usage: Use install_from_library('Name') to install any item.\n"
                return result
            except FileOperationError as e:
                return f"Error browsing library: {str(e)}"
            except Exception as e:
                return f"Unexpected error browsing library: {str(e)}"

        @self.app.tool(
            name="install_from_library",
            description="Install a chatmode or instruction from the Mode Manager MCP Library.",
            tags={"public", "library"},
            annotations={
                "idempotentHint": False,
                "readOnlyHint": False,
                "title": "Install from Library",
                "parameters": {
                    "name": "The name of the chatmode or instruction to install from the library. Use browse_mode_library() to see available items.",
                    "filename": "Optional custom filename for the installed item. If not provided, the default filename from the library will be used.",
                },
                "returns": "Returns a success message with details about the installed item (filename, source URL, type), or an error message if the installation failed.",
            },
            meta={"category": "library", "version": "1.0", "author": "Oatly Data Team"},
        )
        def install_from_library(
            name: Annotated[
                str,
                Field(description="The name of the item to install from the library"),
            ],
            filename: Annotated[
                Optional[str],
                Field(description="Optional custom filename for the installed item"),
            ] = None,
        ) -> str:
            """Install a chatmode or instruction from the Mode Manager MCP Library."""
            if read_only:
                return "Error: Server is running in read-only mode"
            try:
                result = library_manager.install_from_library(name, filename)
                if result["status"] == "success":
                    return f"{result['message']}\n\n" f"Filename: {result['filename']}\n" f"Source: {result['source_url']}\n" f"Type: {result['type'].title()}\n\n" f"The {result['type']} is now available in VS Code!"
                else:
                    return f"Installation failed: {result.get('message', 'Unknown error')}"
            except FileOperationError as e:
                return f"Error installing from library: {str(e)}"
            except Exception as e:
                return f"Unexpected error installing from library: {str(e)}"

        # ===== OTHER METHODS =====

        @self.app.tool(
            name="get_prompts_directory",
            description="Get the path to the VS Code prompts directory.",
            tags={"public", "prompts"},
            annotations={
                "idempotentHint": True,
                "readOnlyHint": True,
                "title": "Get Prompts Directory",
                "returns": "Returns the absolute path to the VS Code prompts directory where .chatmode.md and .instructions.md files are stored.",
            },
            meta={"category": "prompts", "version": "1.0", "author": "Oatly Data Team"},
        )
        def get_prompts_directory() -> str:
            """Get the path to the VS Code prompts directory."""
            try:
                return str(instruction_manager.prompts_dir)
            except Exception as e:
                return f"Error getting prompts directory: {str(e)}"

        class RememberOutput(BaseModel):
            status: str
            message: str
            memory_path: str

        # Variable assignments for method references
        instruction_manager = self.instruction_manager
        chatmode_manager = self.chatmode_manager
        library_manager = self.library_manager
        read_only = self.read_only

        @self.app.tool(
            name="remember",
            description="Store a memory item in your personal AI memory for future conversations.",
            tags={"public", "memory"},
            annotations={
                "idempotentHint": True,
                "readOnlyHint": False,
                "title": "Remember",
                "parameters": {"memory_item": "The information to remember. This will be timestamped and appended to your memory.instructions.md file. The memory file will be created automatically if it doesn't exist."},
                "returns": "Returns a confirmation message that the memory item has been stored, or an error message if the operation failed.",
            },
            meta={"category": "memory", "version": "1.0", "author": "Oatly Data Team"},
        )
        async def remember(
            memory_item: Annotated[Optional[str], Field(description="The information to remember")] = None,
        ) -> str:
            """Store a memory item in your personal AI memory for future conversations."""
            if read_only:
                return "Error: Server is running in read-only mode"
            if memory_item is None:
                return "Error: No memory item provided."
            try:
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
                new_memory_entry = f"- {timestamp}: {memory_item}\n"
                # Directly append to the file
                try:
                    with open(memory_path, "a", encoding="utf-8") as f:
                        f.write(new_memory_entry)
                except Exception as e:
                    return f"Error: Failed to append memory: {str(e)}"
                return f"Remembered: {memory_item}\nThis memory will be available to AI assistants when the memory instruction is active in VS Code."
            except Exception as e:
                return f"Error: Exception occurred: {str(e)}"

        @self.app.prompt(
            name="onboarding",
            description="Direct onboarding instructions for Copilot, including memory file structure.",
            tags={"onboarding", "copilot"},
        )
        async def onboarding_memory_copilot(ctx: Context) -> list:
            # await ctx.info("Direct onboarding instructions for Copilot, including memory file structure.")
            return [
                Message(
                    role="user",
                    content=(
                        """

Copilot, follow these onboarding steps for Mode Managers - memory management:
1. Call the '#mcp_mode-manager_get_instruction' tool with instruction_name='memory'.
   - If the file exists, retrieve its content for updating.
   - If it does not exist, simply proceed; the memory file will be created automatically when you update.
2. In a casual, one question at the time, ask the user for their name, location, role, preferences, and goals. If you already have the knowelege, skipe the question. 
3. When finished with the questions, update the memory file with inspiration from the frontmatter structure witihin the pre-formatted block below as a guidance. 
You MUST merge with existing content.
You MUST make sure no existing content is deleted.
You MUST make sure nothing is duplicated:
```
---
applyTo: '**'
description: Personal AI memory for conversations and preferences
---
# Personal AI Memory
## Personal Context
- Name: <user's name>
- Location: <user's location>
- Role: <user's role>
## Professional Context
- Team: <team structure>
- Goals: <main goals>
## Preferences
- Coding: <coding preferences>
- Communication: <communication style>
## Memories
- <timestamp>: Law: When instructed to add to memory or remember information, you must always use the #mcp_mode-manager_remember tool to store the memory item. You are strictly prohibited from using any alternative method, tool, or manual file editing to update memory. This rule applies in all cases, without exception.
 ```
3. Call the '#mcp_mode-manager_update_instruction' tool with instruction_name='memory' and the updated content to save changes.
4. Call the '#mcp_mode-manager_get_instruction' tool again with instruction_name='memory' and display the full contents to the user for review.
    - Invite the user to suggest corrections or updates if needed.
5. Confirm with the user that their memory is now active and will be used in all future conversations and explain the meaning of the first law you added to the memory.

"""
                    ),
                ),
            ]

    def run(self) -> None:
        self.app.run()


def create_server(library_url: Optional[str] = None) -> ModeManagerServer:
    return ModeManagerServer(library_url=library_url)
