"""Tools for managing VS Code .chatmode.md files."""

from typing import Annotated, Optional

from ..server_registry import get_server_registry


def register_chatmode_tools() -> None:
    """Register all chatmode-related tools with the server."""
    registry = get_server_registry()
    app = registry.app
    chatmode_manager = registry.chatmode_manager
    read_only = registry.read_only

    @app.tool(
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
        },
    )
    def create_chatmode(
        filename: Annotated[str, "The filename for the new chatmode (with or without extension)"],
        description: Annotated[str, "A brief description of what this chatmode does"],
        content: Annotated[str, "The main content/instructions for the chatmode in markdown format"],
        tools: Annotated[Optional[str], "Optional comma-separated list of tool names"] = None,
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

    @app.tool(
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

    @app.tool(
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
        },
    )
    def get_chatmode(
        filename: Annotated[str, "The filename of the chatmode to retrieve (with or without extension)"],
    ) -> str:
        """Get the raw content of a VS Code .chatmode.md file."""
        try:
            if not filename.endswith(".chatmode.md"):
                filename += ".chatmode.md"
            raw_content = chatmode_manager.get_raw_chatmode(filename)
            return raw_content
        except Exception as e:
            return f"Error getting VS Code chatmode '{filename}': {str(e)}"

    @app.tool(
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
        },
    )
    def update_chatmode(
        filename: Annotated[str, "The filename of the chatmode to update (with or without extension)"],
        description: Annotated[Optional[str], "Optional new description for the chatmode"] = None,
        content: Annotated[Optional[str], "Optional new content for the chatmode"] = None,
        tools: Annotated[Optional[str], "Optional new comma-separated list of tool names"] = None,
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

    @app.tool(
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
        },
    )
    def delete_chatmode(
        filename: Annotated[str, "The filename of the chatmode to delete (with or without extension)"],
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

    @app.tool(
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
        },
    )
    def update_chatmode_from_source(
        filename: Annotated[str, "The filename of the chatmode to update from source (with or without extension)"],
    ) -> str:
        """Update a .chatmode.md file from its source definition."""
        return "Not implemented"
