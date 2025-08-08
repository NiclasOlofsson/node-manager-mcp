"""Unit tests for simple_file_ops module."""

import pytest

from mode_manager_mcp.simple_file_ops import FileOperationError, parse_frontmatter


class TestParseFrontmatter:
    """Test cases for parse_frontmatter function."""

    def test_parse_frontmatter_with_apply_to_quoted(self) -> None:
        """Test parsing frontmatter with applyTo field using single quotes."""
        content = """---
applyTo: '**'
description: Test description
---
This is the content body.
"""
        frontmatter, body = parse_frontmatter(content)

        # This is correct YAML behavior: quotes are delimiters, content is the string value
        assert frontmatter["applyTo"] == "**"
        assert frontmatter["description"] == "Test description"
        assert body == "This is the content body.\n"

    def test_parse_frontmatter_with_apply_to_double_quoted(self) -> None:
        """Test parsing frontmatter with applyTo field using double quotes."""
        content = """---
applyTo: "**"
description: Test description
---
This is the content body.
"""
        frontmatter, body = parse_frontmatter(content)

        # This is correct YAML behavior: quotes are delimiters, content is the string value
        assert frontmatter["applyTo"] == "**"
        assert frontmatter["description"] == "Test description"
        assert body == "This is the content body.\n"

    def test_parse_frontmatter_with_apply_to_unquoted(self) -> None:
        """Test parsing frontmatter with applyTo field without quotes."""
        content = """---
applyTo: **
description: Test description
---
This is the content body.
"""
        frontmatter, body = parse_frontmatter(content)

        assert frontmatter["applyTo"] == "**"
        assert frontmatter["description"] == "Test description"
        assert body == "This is the content body.\n"

    def test_parse_frontmatter_preserve_quotes_in_complex_values(self) -> None:
        """Test YAML parsing behavior with various quote scenarios."""
        content = """---
applyTo: '**'
pattern: 'src/**/*.py'
command: "echo 'hello world'"
simple: value
---
Content here.
"""
        frontmatter, body = parse_frontmatter(content)

        # This shows correct YAML behavior: quotes are delimiters, not content
        # The semantic meaning is preserved: these are all string values
        assert frontmatter["applyTo"] == "**"  # Glob pattern as string
        assert frontmatter["pattern"] == "src/**/*.py"  # File pattern as string
        assert frontmatter["command"] == "echo 'hello world'"  # Command with embedded quotes
        assert frontmatter["simple"] == "value"  # Unquoted string
        assert body == "Content here.\n"

    def test_parse_frontmatter_no_frontmatter(self) -> None:
        """Test parsing content without frontmatter."""
        content = "Just plain content without frontmatter."

        frontmatter, body = parse_frontmatter(content)

        assert frontmatter == {}
        assert body == "Just plain content without frontmatter."

    def test_parse_frontmatter_malformed(self) -> None:
        """Test parsing malformed frontmatter (missing closing ---)."""
        content = """---
applyTo: '**'
description: Test
This content has malformed frontmatter.
"""
        frontmatter, body = parse_frontmatter(content)

        # Should return empty dict and full content when malformed
        assert frontmatter == {}
        assert body == content

    def test_parse_frontmatter_empty_frontmatter(self) -> None:
        """Test parsing with empty frontmatter."""
        content = """---
---
Content after empty frontmatter.
"""
        frontmatter, body = parse_frontmatter(content)

        assert frontmatter == {}
        assert body == "Content after empty frontmatter.\n"

    def test_parse_frontmatter_with_comments(self) -> None:
        """Test parsing frontmatter with YAML comments."""
        content = """---
# This is a comment
applyTo: '**'
# Another comment
description: Test description
---
Content body.
"""
        frontmatter, body = parse_frontmatter(content)

        assert frontmatter["applyTo"] == "**"
        assert frontmatter["description"] == "Test description"
        assert body == "Content body.\n"

    def test_parse_frontmatter_boolean_values(self) -> None:
        """Test parsing boolean values in frontmatter."""
        content = """---
enabled: true
disabled: false
applyTo: '**'
---
Content.
"""
        frontmatter, body = parse_frontmatter(content)

        assert frontmatter["enabled"] is True
        assert frontmatter["disabled"] is False
        assert frontmatter["applyTo"] == "**"
        assert body == "Content.\n"

    def test_parse_frontmatter_integer_values(self) -> None:
        """Test parsing integer values in frontmatter."""
        content = """---
count: 42
version: 1
applyTo: '**'
---
Content.
"""
        frontmatter, body = parse_frontmatter(content)

        assert frontmatter["count"] == 42
        assert frontmatter["version"] == 1
        assert frontmatter["applyTo"] == "**"
        assert body == "Content.\n"

    def test_parse_frontmatter_list_values(self) -> None:
        """Test parsing list values in frontmatter."""
        content = """---
tools: ["tool1", "tool2", "tool3"]
applyTo: '**'
---
Content.
"""
        frontmatter, body = parse_frontmatter(content)

        assert frontmatter["tools"] == ["tool1", "tool2", "tool3"]
        assert frontmatter["applyTo"] == "**"
        assert body == "Content.\n"

    def test_parse_frontmatter_quote_stripping_demonstration(self) -> None:
        """
        Demonstrate the quote-stripping behavior for applyTo field.

        This test shows that the current implementation strips quotes from
        single-quoted and double-quoted strings, which is CORRECT YAML behavior.
        In YAML, quotes are delimiters that indicate string literals, but they are
        not part of the content itself.

        For example:
        - applyTo: '**'  → YAML string value: "**"
        - applyTo: "**"  → YAML string value: "**"
        - applyTo: **    → YAML string value: "**"

        All three should result in the same parsed value: "**"
        """
        # Test single quotes
        content_single = """---
applyTo: '**'
---
Content.
"""
        frontmatter, _ = parse_frontmatter(content_single)

        # This is CORRECT behavior: quotes are YAML delimiters, not content
        assert frontmatter["applyTo"] == "**"

        # Test double quotes
        content_double = """---
applyTo: "**"
---
Content.
"""
        frontmatter, _ = parse_frontmatter(content_double)

        # This is CORRECT behavior: quotes are YAML delimiters, not content
        assert frontmatter["applyTo"] == "**"

        # Test unquoted (should remain the same)
        content_unquoted = """---
applyTo: **
---
Content.
"""
        frontmatter, _ = parse_frontmatter(content_unquoted)

        # This should remain unchanged
        assert frontmatter["applyTo"] == "**"

        # Test that all three approaches produce the same semantic result
        assert frontmatter["applyTo"] == "**"


def test_write_frontmatter_file_glob_patterns() -> None:
    """Test that YAML frontmatter handles glob patterns correctly."""
    import tempfile
    from pathlib import Path

    from mode_manager_mcp.simple_file_ops import write_frontmatter_file
    
    temp_file = Path(tempfile.mktemp())

    # Test different glob patterns and quoting behavior
    test_cases = [
        # (value, expected_in_yaml, description)
        ("**", "applyTo: '**'", "Bare ** should be quoted"),
        ("**/*.py", "applyTo: '**/*.py'", "Glob pattern should be quoted per GitHub requirements"),
        ("**/src/**", "applyTo: '**/src/**'", "Complex glob pattern should be quoted per GitHub requirements"),
        ("*/test.js", "applyTo: '*/test.js'", "Simple glob pattern should be quoted per GitHub requirements"),
        ("Test: description", "description: 'Test: description'", "String with colon should be quoted"),
    ]
    
    for value, expected_yaml, description in test_cases:
        if "applyTo" in expected_yaml:
            frontmatter = {"applyTo": value}
        else:
            frontmatter = {"description": value}
        
        content = "Test content"
        
        # Write file
        assert write_frontmatter_file(temp_file, frontmatter, content, create_backup=False) is True
        
        # Read raw content and check formatting
        raw_content = temp_file.read_text()
        assert expected_yaml in raw_content, f"{description}: Expected '{expected_yaml}' in:\n{raw_content}"
    
    # Clean up
    if temp_file.exists():
        temp_file.unlink()
