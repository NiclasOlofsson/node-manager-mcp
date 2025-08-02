"""
Path utilities for VS Code and system directory detection.

This module provides utilities for finding VS Code configuration directories
and handling cross-platform path operations.
"""

import logging
import os
import platform
import types
from pathlib import Path
from typing import Any, Optional

import psutil


def detect_vscode_variant() -> Optional[str]:
    # psutil is always present
    try:
        parent = psutil.Process(os.getppid())
        proc_name = parent.name().lower()
    except Exception as e:
        logger.error(f"Error detecting VS Code variant: {e}")
        return None
    if "insiders" in proc_name:
        return "insiders"
    elif "code" in proc_name:
        return "stable"
    return None


logger = logging.getLogger(__name__)


def get_vscode_user_directory() -> Path:
    """
    Get the VS Code user directory for the current platform.

    Returns:
        Path to VS Code user directory

    Raises:
        OSError: If VS Code directory cannot be found
    """
    system = platform.system()
    variant = detect_vscode_variant()

    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            insiders_dir = Path(appdata) / "Code - Insiders" / "User"
            stable_dir = Path(appdata) / "Code" / "User"
        else:
            localappdata = os.environ.get(
                "LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")
            )
            insiders_dir = (
                Path(localappdata) / "Programs" / "Microsoft VS Code Insiders" / "User"
            )
            stable_dir = Path(localappdata) / "Programs" / "Microsoft VS Code" / "User"

    elif system == "Darwin":
        insiders_dir = (
            Path.home() / "Library" / "Application Support" / "Code - Insiders" / "User"
        )
        stable_dir = Path.home() / "Library" / "Application Support" / "Code" / "User"

    else:
        config_home = os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
        insiders_dir = Path(config_home) / "Code - Insiders" / "User"
        stable_dir = Path(config_home) / "Code" / "User"

    # Use detected variant if possible
    if variant == "insiders":
        logger.debug(f"VS Code Insiders user directory (by process): {insiders_dir}")
        return insiders_dir
    elif variant == "stable":
        logger.debug(f"VS Code stable user directory (by process): {stable_dir}")
        return stable_dir
    # Fallback: Prefer Insiders if present
    if insiders_dir.exists():
        logger.debug(f"VS Code Insiders user directory: {insiders_dir}")
        return insiders_dir
    logger.debug(f"VS Code stable user directory: {stable_dir}")
    return stable_dir


def get_vscode_prompts_directory() -> Path:
    """
    Get the VS Code prompts directory.

    Returns:
        Path to prompts directory (creates if not exists)
    """
    user_dir = get_vscode_user_directory()
    prompts_dir = user_dir / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    logger.debug(f"VS Code prompts directory: {prompts_dir}")
    return prompts_dir


def find_vscode_executable() -> Optional[Path]:
    """
    Find the VS Code executable on the current system.

    Returns:
        Path to VS Code executable if found, None otherwise
    """
    system = platform.system()

    possible_paths = []

    if system == "Windows":
        # Common Windows installation paths
        possible_paths = [
            Path(os.environ.get("PROGRAMFILES", "C:\\Program Files"))
            / "Microsoft VS Code"
            / "Code.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"))
            / "Microsoft VS Code"
            / "Code.exe",
            Path(
                os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
            )
            / "Programs"
            / "Microsoft VS Code"
            / "Code.exe",
        ]

    elif system == "Darwin":
        # macOS paths
        possible_paths = [
            Path(
                "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"
            ),
            Path("/usr/local/bin/code"),
        ]

    else:
        # Linux paths
        possible_paths = [
            Path("/usr/bin/code"),
            Path("/usr/local/bin/code"),
            Path("/snap/code/current/usr/share/code/bin/code"),
            Path(os.path.expanduser("~/.local/bin/code")),
        ]

    # Check each possible path
    for path in possible_paths:
        if path.exists() and path.is_file():
            logger.debug(f"Found VS Code executable: {path}")
            return path

    # Try to find in PATH
    import shutil

    code_path = shutil.which("code")
    if code_path:
        logger.debug(f"Found VS Code executable in PATH: {code_path}")
        return Path(code_path)

    logger.warning("VS Code executable not found")
    return None


def ensure_directory(path: Path) -> bool:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure

    Returns:
        True if directory exists or was created successfully
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {e}")
        return False


def is_vscode_workspace(path: Path) -> bool:
    """
    Check if a path is a VS Code workspace.

    Args:
        path: Path to check

    Returns:
        True if path contains VS Code workspace files
    """
    if not path.is_dir():
        return False

    # Check for .vscode directory
    vscode_dir = path / ".vscode"
    if vscode_dir.exists() and vscode_dir.is_dir():
        return True

    # Check for .code-workspace files
    for file_path in path.glob("*.code-workspace"):
        if file_path.is_file():
            return True

    return False


def get_workspace_settings_path(workspace_path: Path) -> Optional[Path]:
    """
    Get the settings.json path for a VS Code workspace.

    Args:
        workspace_path: Path to workspace directory

    Returns:
        Path to settings.json if workspace exists, None otherwise
    """
    if not is_vscode_workspace(workspace_path):
        return None

    settings_path = workspace_path / ".vscode" / "settings.json"
    return settings_path if settings_path.parent.exists() else None
