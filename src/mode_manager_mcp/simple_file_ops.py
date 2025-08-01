"""
Simple file operations for mode management.

This module provides basic file operations with frontmatter support
for chatmode and instruction files.
"""

import json
import logging
import re
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class FileOperationError(Exception):
    """Exception raised for file operation errors."""

    pass


def parse_frontmatter_file(file_path: Union[str, Path]) -> Tuple[Dict[str, Any], str]:
    """
    Parse a file with YAML frontmatter.

    Args:
        file_path: Path to the file

    Returns:
        Tuple of (frontmatter_dict, content_string)

    Raises:
        FileOperationError: If file cannot be parsed
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        raise FileOperationError(f"Could not read file {file_path}: {e}")

    # Check for frontmatter
    if not content.startswith("---\n"):
        # No frontmatter, return empty dict and full content
        return {}, content

    # Find the end of frontmatter
    end_match = re.search(r"\n---\n", content)
    if not end_match:
        # Malformed frontmatter, treat as no frontmatter
        return {}, content

    frontmatter_content = content[4 : end_match.start()]
    body_content = content[end_match.end() :]

    try:
        # Simple YAML parsing for basic frontmatter
        frontmatter = {}
        for line in frontmatter_content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                # Handle different value types
                if value.startswith("[") and value.endswith("]"):
                    # List value
                    try:
                        frontmatter[key] = json.loads(value)
                    except json.JSONDecodeError:
                        # Simple list parsing
                        items = value[1:-1].split(",")
                        frontmatter[key] = [
                            item.strip().strip("\"'") for item in items if item.strip()
                        ]
                elif value.startswith('"') and value.endswith('"'):
                    # Quoted string
                    frontmatter[key] = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    # Quoted string
                    frontmatter[key] = value[1:-1]
                elif value.lower() in ("true", "false"):
                    # Boolean
                    frontmatter[key] = value.lower() == "true"
                elif value.isdigit():
                    # Integer
                    frontmatter[key] = int(value)
                else:
                    # String
                    frontmatter[key] = value

        return frontmatter, body_content

    except Exception as e:
        logger.warning(f"Error parsing frontmatter in {file_path}: {e}")
        return {}, content


def write_frontmatter_file(
    file_path: Union[str, Path],
    frontmatter: Dict[str, Any],
    content: str,
    create_backup: bool = True,
) -> bool:
    """
    Write a file with YAML frontmatter.

    Args:
        file_path: Path to write the file
        frontmatter: Dictionary of frontmatter data
        content: Main content of the file
        create_backup: Whether to create a backup before overwriting (default: True)

    Returns:
        True if successful

    Raises:
        FileOperationError: If file cannot be written
    """
    try:
        # Create backup if file exists and backup is requested
        file_path = Path(file_path)
        if create_backup and file_path.exists():
            import datetime

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = (
                file_path.parent
                / f"{file_path.stem}.backup_{timestamp}{file_path.suffix}"
            )

            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup before write: {backup_path}")

        # Create frontmatter YAML
        frontmatter_lines = ["---"]

        for key, value in frontmatter.items():
            if isinstance(value, list):
                # Format list as JSON array for simplicity
                frontmatter_lines.append(f"{key}: {json.dumps(value)}")
            elif isinstance(value, str):
                # Quote strings that contain special characters
                if ":" in value or "\n" in value or value.startswith(('"', "'")):
                    frontmatter_lines.append(f'{key}: "{value}"')
                else:
                    frontmatter_lines.append(f"{key}: {value}")
            elif isinstance(value, bool):
                frontmatter_lines.append(f"{key}: {str(value).lower()}")
            else:
                frontmatter_lines.append(f"{key}: {value}")

        frontmatter_lines.append("---")

        # Combine frontmatter and content
        full_content = "\n".join(frontmatter_lines) + "\n" + content

        # Ensure parent directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        # Write file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_content)

        logger.debug(f"Successfully wrote file: {file_path}")
        return True

    except Exception as e:
        raise FileOperationError(f"Could not write file {file_path}: {e}")


def write_file_with_backup(
    file_path: Union[str, Path], content: str, create_backup: bool = True
) -> bool:
    """
    Write a file with optional backup.

    Args:
        file_path: Path to write the file
        content: Content to write
        create_backup: Whether to create a backup before overwriting (default: True)

    Returns:
        True if successful

    Raises:
        FileOperationError: If file cannot be written
    """
    try:
        # Create backup if file exists and backup is requested
        file_path = Path(file_path)
        if create_backup and file_path.exists():
            import datetime

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = (
                file_path.parent
                / f"{file_path.stem}.backup_{timestamp}{file_path.suffix}"
            )

            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup before write: {backup_path}")

        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.debug(f"Successfully wrote file: {file_path}")
        return True

    except Exception as e:
        raise FileOperationError(f"Could not write file {file_path}: {e}")


def safe_delete_file(file_path: Union[str, Path], create_backup: bool = True) -> bool:
    """
    Safely delete a file with optional backup.

    Args:
        file_path: Path to the file to delete
        create_backup: Whether to create a backup before deletion

    Returns:
        True if successful

    Raises:
        FileOperationError: If file cannot be deleted
    """
    file_path = Path(file_path)

    if not file_path.exists():
        logger.warning(f"File does not exist: {file_path}")
        return True

    try:
        if create_backup:
            # Create backup with timestamp
            import datetime

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = (
                file_path.parent
                / f"{file_path.stem}.backup_{timestamp}{file_path.suffix}"
            )

            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup: {backup_path}")

        # Delete the file
        file_path.unlink()
        logger.info(f"Deleted file: {file_path}")
        return True

    except Exception as e:
        raise FileOperationError(f"Could not delete file {file_path}: {e}")


def copy_file(src_path: Union[str, Path], dst_path: Union[str, Path]) -> bool:
    """
    Copy a file from source to destination.

    Args:
        src_path: Source file path
        dst_path: Destination file path

    Returns:
        True if successful

    Raises:
        FileOperationError: If file cannot be copied
    """
    try:
        src_path = Path(src_path)
        dst_path = Path(dst_path)

        if not src_path.exists():
            raise FileOperationError(f"Source file does not exist: {src_path}")

        # Ensure destination directory exists
        dst_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy the file
        shutil.copy2(src_path, dst_path)
        logger.debug(f"Copied file: {src_path} -> {dst_path}")
        return True

    except Exception as e:
        raise FileOperationError(f"Could not copy file {src_path} to {dst_path}: {e}")


def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Get information about a file.

    Args:
        file_path: Path to the file

    Returns:
        Dictionary with file information

    Raises:
        FileOperationError: If file cannot be accessed
    """
    try:
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileOperationError(f"File does not exist: {file_path}")

        stat = file_path.stat()

        return {
            "path": str(file_path),
            "name": file_path.name,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "created": stat.st_ctime,
            "is_file": file_path.is_file(),
            "is_dir": file_path.is_dir(),
            "suffix": file_path.suffix,
            "stem": file_path.stem,
        }

    except Exception as e:
        raise FileOperationError(f"Could not get file info for {file_path}: {e}")


def read_text_file(file_path: Union[str, Path]) -> str:
    """
    Read a text file with proper encoding handling.

    Args:
        file_path: Path to the file

    Returns:
        File content as string

    Raises:
        FileOperationError: If file cannot be read
    """
    try:
        file_path = Path(file_path)

        # Try different encodings
        for encoding in ["utf-8", "utf-8-sig", "cp1252", "latin1"]:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue

        raise FileOperationError(
            f"Could not decode file with any supported encoding: {file_path}"
        )

    except Exception as e:
        raise FileOperationError(f"Could not read file {file_path}: {e}")


def write_text_file(file_path: Union[str, Path], content: str) -> bool:
    """
    Write content to a text file.

    Args:
        file_path: Path to write the file
        content: Content to write

    Returns:
        True if successful

    Raises:
        FileOperationError: If file cannot be written
    """
    try:
        file_path = Path(file_path)

        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.debug(f"Successfully wrote text file: {file_path}")
        return True

    except Exception as e:
        raise FileOperationError(f"Could not write file {file_path}: {e}")
