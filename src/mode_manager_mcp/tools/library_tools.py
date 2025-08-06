"""Tools for managing the Mode Manager MCP Library."""

from typing import Annotated, Optional

from ..instruction_manager import INSTRUCTION_FILE_EXTENSION
from ..server_registry import get_server_registry
from ..simple_file_ops import FileOperationError


def register_library_tools() -> None:
    """Register all library-related tools with the server."""
    registry = get_server_registry()
    app = registry.app
    library_manager = registry.library_manager
    read_only = registry.read_only

    @app.tool(
        name="refresh_library",
        description="Refresh the Mode Manager MCP Library from its source URL.",
        tags={"public", "library"},
        annotations={
            "idempotentHint": True,
            "readOnlyHint": True,
            "title": "Refresh Library",
            "returns": "Returns information about the library refresh operation, including library name, version, last updated date, and counts of available chatmodes and instructions. Also provides usage instructions.",
        },
        meta={"category": "library"},
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

    @app.tool(
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
        meta={"category": "library"},
    )
    def browse_mode_library(
        category: Annotated[Optional[str], "Optional category filter"] = None,
        search: Annotated[Optional[str], "Optional search term"] = None,
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

    @app.tool(
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
        meta={"category": "library"},
    )
    def install_from_library(
        name: Annotated[str, "The name of the item to install from the library"],
        filename: Annotated[Optional[str], "Optional custom filename for the installed item"] = None,
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
