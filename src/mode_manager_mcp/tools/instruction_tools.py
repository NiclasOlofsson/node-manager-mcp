"""Tools for managing VS Code .instructions.md files."""

from typing import Annotated, Optional

from ..instruction_manager import INSTRUCTION_FILE_EXTENSION
from ..server_registry import get_server_registry


def register_instruction_tools() -> None:
    """Register all instruction-related tools with the server."""
    registry = get_server_registry()
    app = registry.app
    instruction_manager = registry.instruction_manager
    read_only = registry.read_only

    @app.tool(
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
        },
    )
    def create_instruction(
        instruction_name: Annotated[str, "The name for the new instruction (with or without extension)"],
        description: Annotated[str, "A brief description of what this instruction does"],
        content: Annotated[str, "The main content/instructions in markdown format"],
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

    @app.tool(
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

    @app.tool(
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
        },
    )
    def get_instruction(
        instruction_name: Annotated[str, "Name of the instruction (without extension)"],
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

    @app.tool(
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
        },
    )
    def update_instruction(
        instruction_name: Annotated[str, "The name of the instruction to update (with or without extension)"],
        description: Annotated[Optional[str], "Optional new description for the instruction"] = None,
        content: Annotated[Optional[str], "Optional new content for the instruction"] = None,
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

    @app.tool(
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
        },
    )
    def delete_instruction(
        instruction_name: Annotated[str, "The name of the instruction to delete (with or without extension)"],
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
