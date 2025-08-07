"""Type definitions and enums for Mode Manager MCP."""

from enum import Enum


class MemoryScope(str, Enum):
    """Enum for memory scope values."""

    user = "user"
    workspace = "workspace"

    def __str__(self) -> str:
        """Return the string value for easy use in messages."""
        return self.value


class LanguagePattern:
    """Language-specific file patterns for applyTo field."""

    PATTERNS = {
        "python": "**/*.py",
        "javascript": "**/*.js",
        "typescript": "**/*.ts",
        "csharp": "**/*.cs",
        "java": "**/*.java",
        "cpp": "**/*.{cpp,hpp,cc,cxx}",
        "c": "**/*.{c,h}",
        "go": "**/*.go",
        "rust": "**/*.rs",
        "sql": "**/*.sql",
        "html": "**/*.html",
        "css": "**/*.css",
        "scss": "**/*.scss",
        "json": "**/*.json",
        "yaml": "**/*.{yml,yaml}",
        "markdown": "**/*.md",
        "shell": "**/*.{sh,bash}",
        "powershell": "**/*.ps1",
    }

    @classmethod
    def get_pattern(cls, language: str) -> str:
        """Get the applyTo pattern for a language."""
        return cls.PATTERNS.get(language.lower(), f"**/*.{language.lower()}")

    @classmethod
    def get_all_pattern(cls) -> str:
        """Get the pattern that applies to all files."""
        return "**"
