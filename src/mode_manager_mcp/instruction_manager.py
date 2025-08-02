"""
Mode Manager for VS Code .instructions.md files.

This module handles instruction files which define custom instructions
and workspace-specific AI guidance for VS Code Copilot.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .path_utils import get_vscode_prompts_directory
from .simple_file_ops import (
    FileOperationError,
    parse_frontmatter_file,
    safe_delete_file,
    write_frontmatter_file,
)

logger = logging.getLogger(__name__)


INSTRUCTION_FILE_EXTENSION = ".instructions.md"


class InstructionManager:
    def append_to_section(
        self,
        filename: str,
        section_header: str,
        new_entry: str,
    ) -> bool:
        """
        Append a new entry to a specific section in an instruction file.

        Args:
            filename: Name of the .instructions.md file
            section_header: Section header to append to (e.g., '## Memories')
            new_entry: Content to append (should include any formatting, e.g., '- ...')

        Returns:
            True if successful

        Raises:
            FileOperationError: If file cannot be updated
        """
        # Ensure filename has correct extension
        if not filename.endswith(INSTRUCTION_FILE_EXTENSION):
            filename += INSTRUCTION_FILE_EXTENSION

        file_path = self.prompts_dir / filename

        if not file_path.exists():
            raise FileOperationError(f"Instruction file not found: {filename}")

        try:
            current_frontmatter, current_content = parse_frontmatter_file(file_path)
            lines = current_content.splitlines()
            section_start = None
            for i, line in enumerate(lines):
                if line.strip().lower() == section_header.strip().lower():
                    section_start = i
                    break

            if section_start is not None:
                # Find the end of the section (next section header or end of file)
                insert_at = len(lines)
                for j in range(section_start + 1, len(lines)):
                    if lines[j].startswith("## "):
                        insert_at = j
                        break
                # Remove trailing blank line before inserting if present
                if insert_at > section_start + 1 and lines[insert_at - 1].strip() == "":
                    del lines[insert_at - 1]
                    insert_at -= 1
                # Insert the new entry at the end of the section
                lines.insert(insert_at, new_entry)
                new_content = "\n".join(lines)
                if not new_content.endswith("\n"):
                    new_content += "\n"
            else:
                # If section does not exist, append at end
                new_content = (
                    current_content.rstrip("\n") + f"\n{section_header}\n{new_entry}\n"
                )

            success = write_frontmatter_file(
                file_path, current_frontmatter, new_content, create_backup=True
            )
            if success:
                logger.info(f"Appended to section '{section_header}' in: {filename}")
            return success

        except Exception as e:
            raise FileOperationError(
                f"Error appending to section '{section_header}' in {filename}: {e}"
            )

    """
    Manages VS Code .instructions.md files in the prompts directory.
    """

    def __init__(self, prompts_dir: Optional[Union[str, Path]] = None):
        """
        Initialize instruction manager.

        Args:
            prompts_dir: Custom prompts directory (default: VS Code user dir + prompts)
        """
        if prompts_dir:
            self.prompts_dir = Path(prompts_dir)
        else:
            self.prompts_dir = get_vscode_prompts_directory()

        # Ensure prompts directory exists
        self.prompts_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"Instruction manager initialized with prompts directory: {self.prompts_dir}"
        )

    def list_instructions(self) -> List[Dict[str, Any]]:
        """
        List all .instructions.md files in the prompts directory.

        Returns:
            List of instruction file information
        """
        instructions: List[Dict[str, Any]] = []

        if not self.prompts_dir.exists():
            return instructions

        for file_path in self.prompts_dir.glob(f"*{INSTRUCTION_FILE_EXTENSION}"):
            try:
                frontmatter, content = parse_frontmatter_file(file_path)

                # Get preview of content (first 100 chars)
                content_preview = content.strip()[:100] if content.strip() else ""

                instruction_info = {
                    "filename": file_path.name,
                    "name": file_path.name.replace(INSTRUCTION_FILE_EXTENSION, ""),
                    "path": str(file_path),
                    "description": frontmatter.get("description", ""),
                    "frontmatter": frontmatter,
                    "content_preview": content_preview,
                    "size": file_path.stat().st_size,
                    "modified": file_path.stat().st_mtime,
                }

                instructions.append(instruction_info)

            except Exception as e:
                logger.warning(f"Error reading instruction file {file_path}: {e}")
                continue

        # Sort by name
        instructions.sort(key=lambda x: x["name"].lower())
        return instructions

    def get_instruction(self, filename: str) -> Dict[str, Any]:
        """
        Get content and metadata of a specific instruction file.

        Args:
            filename: Name of the .instructions.md file

        Returns:
            Instruction data including frontmatter and content

        Raises:
            FileOperationError: If file cannot be read
        """

        # Ensure filename has correct extension
        if not filename.endswith(INSTRUCTION_FILE_EXTENSION):
            filename += INSTRUCTION_FILE_EXTENSION

        file_path = self.prompts_dir / filename

        if not file_path.exists():
            raise FileOperationError(f"Instruction file not found: {filename}")

        try:
            frontmatter, content = parse_frontmatter_file(file_path)

            return {
                "filename": filename,
                "name": filename.replace(INSTRUCTION_FILE_EXTENSION, ""),
                "path": str(file_path),
                "description": frontmatter.get("description", ""),
                "frontmatter": frontmatter,
                "content": content,
                "size": file_path.stat().st_size,
                "modified": file_path.stat().st_mtime,
            }

        except Exception as e:
            raise FileOperationError(f"Error reading instruction file {filename}: {e}")

    def get_raw_instruction(self, filename: str) -> str:
        """
        Get the raw file content of a specific instruction file without any processing.

        Args:
            filename: Name of the .instructions.md file

        Returns:
            Raw file content as string

        Raises:
            FileOperationError: If file cannot be read
        """

        # Ensure filename has correct extension
        if not filename.endswith(INSTRUCTION_FILE_EXTENSION):
            filename += INSTRUCTION_FILE_EXTENSION

        file_path = self.prompts_dir / filename

        if not file_path.exists():
            raise FileOperationError(f"Instruction file not found: {filename}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

        except Exception as e:
            raise FileOperationError(
                f"Error reading raw instruction file {filename}: {e}"
            )

    def create_instruction(self, filename: str, description: str, content: str) -> bool:
        """
        Create a new instruction file.

        Args:
            filename: Name for the new .instructions.md file
            description: Description of the instruction
            content: Instruction content

        Returns:
            True if successful

        Raises:
            FileOperationError: If file cannot be created
        """

        # Ensure filename has correct extension
        if not filename.endswith(INSTRUCTION_FILE_EXTENSION):
            filename += INSTRUCTION_FILE_EXTENSION

        file_path = self.prompts_dir / filename

        if file_path.exists():
            raise FileOperationError(f"Instruction file already exists: {filename}")

        # Create frontmatter with applyTo field so instructions are actually applied
        frontmatter: Dict[str, Any] = {"applyTo": "**", "description": description}

        try:
            success = write_frontmatter_file(
                file_path, frontmatter, content, create_backup=False
            )
            if success:
                logger.info(f"Created instruction file: {filename}")
            return success

        except Exception as e:
            raise FileOperationError(f"Error creating instruction file {filename}: {e}")

    def update_instruction(
        self,
        filename: str,
        frontmatter: Optional[Dict[str, Any]] = None,
        content: Optional[str] = None,
    ) -> bool:
        """
        Replace the content and/or frontmatter of an instruction file.

        This method is for full rewrites. To append to a section, use append_to_section.

        Args:
            filename: Name of the .instructions.md file
            frontmatter: New frontmatter (optional)
            content: New content (optional, replaces all markdown content)

        Returns:
            True if successful

        Raises:
            FileOperationError: If file cannot be updated
        """
        # Ensure filename has correct extension
        if not filename.endswith(INSTRUCTION_FILE_EXTENSION):
            filename += INSTRUCTION_FILE_EXTENSION

        file_path = self.prompts_dir / filename

        if not file_path.exists():
            raise FileOperationError(f"Instruction file not found: {filename}")

        try:
            # Read current content
            current_frontmatter, current_content = parse_frontmatter_file(file_path)

            # Use provided values or keep current ones
            new_frontmatter = (
                frontmatter if frontmatter is not None else current_frontmatter
            )
            # If new content is provided, replace all markdown content
            if content is not None:
                new_content = content
            else:
                new_content = current_content

            success = write_frontmatter_file(
                file_path, new_frontmatter, new_content, create_backup=True
            )
            if success:
                logger.info(f"Updated instruction file with backup: {filename}")
            return success

        except Exception as e:
            raise FileOperationError(f"Error updating instruction file {filename}: {e}")

    def delete_instruction(self, filename: str) -> bool:
        """
        Delete an instruction file with automatic backup.

        Args:
            filename: Name of the .instructions.md file

        Returns:
            True if successful

        Raises:
            FileOperationError: If file cannot be deleted
        """

        # Ensure filename has correct extension
        if not filename.endswith(INSTRUCTION_FILE_EXTENSION):
            filename += INSTRUCTION_FILE_EXTENSION

        file_path = self.prompts_dir / filename

        if not file_path.exists():
            raise FileOperationError(f"Instruction file not found: {filename}")

        try:
            # Use safe delete which creates backup automatically
            safe_delete_file(file_path, create_backup=True)
            logger.info(f"Deleted instruction file with backup: {filename}")
            return True

        except Exception as e:
            raise FileOperationError(f"Error deleting instruction file {filename}: {e}")
