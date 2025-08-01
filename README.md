# Mode Manager MCP

A Model Context Protocol (MCP) server for managing VS Code `.chatmode.md` and `.instruction.md` files - the prompt files that define custom instructions and tools for GitHub Copilot.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)

## 🎯 Overview

This MCP server provides AI agents with secure, controlled access to VS Code prompt files, enabling them to:

- ✅ Create, read, update, and delete `.chatmode.md` files (chat modes with tools)
- ✅ Create, read, update, and delete `.instruction.md` files (general instructions)
- ✅ **Browse and install from the Mode Manager MCP Library** - curated collection of chatmodes and instructions
- ✅ Update chatmode files from source URLs while preserving local tool customizations
- ✅ Safe deletion with automatic timestamped backups
- ✅ Manage GitHub Copilot prompt configurations with YAML frontmatter
- ✅ List and browse available prompt files by type
- ✅ Safely handle frontmatter and markdown content

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/NiclasOlofsson/node-manager-mcp.git
cd node-manager-mcp

# Install dependencies with pipenv
pipenv install

# Or install with pip
pip install -e .
```

### Usage

#### 1. With Pipenv (Recommended)
```bash
# Run the server
pipenv run python -m src.mode_manager_mcp

# Check version
pipenv run python -m src.mode_manager_mcp --version

# Run tests
pipenv run python test_introspection.py
```

#### 2. With Development Script
```bash
# Test the server
pipenv run python dev.py test

# Check version
pipenv run python dev.py version

# Run the server
pipenv run python dev.py run
```

### VS Code Integration

Add to your VS Code MCP configuration (`.vscode/mcp.json`):

```json
{
  "mcpServers": {
    "mode-manager": {
      "command": "pipenv",
      "args": [
        "run",
        "python", 
        "-m",
        "src.mode_manager_mcp"
      ],
      "cwd": "."
    }
  }
}
```

## 🛠️ Available Tools

### ChatMode Management (.chatmode.md files)
- `list_chatmodes()` - List all chatmode files
- `get_chatmode(filename)` - Get chatmode content
- `create_chatmode(filename, description, content, tools?)` - Create new chatmode
- `update_chatmode(filename, description?, content?, tools?)` - Update existing chatmode
- `delete_chatmode(filename)` - Delete chatmode file
- `update_chatmode_from_source(filename)` - Update from source URL

### Instruction Management (.instruction.md files)
- `list_instructions()` - List all instruction files
- `get_instruction(filename)` - Get instruction content
- `create_instruction(filename, description, content)` - Create new instruction
- `update_instruction(filename, description?, content?)` - Update existing instruction
- `delete_instruction(filename)` - Delete instruction file

### 📚 Library Management (NEW!)
- `browse_mode_library(category?, search?)` - Browse curated library of chatmodes and instructions
- `install_from_library(name, filename?)` - Install chatmode/instruction from library
- `refresh_library()` - Refresh library cache

### Directory Management
- `get_prompts_directory()` - Get prompts directory info and contents

## 📁 File Structure

```
VS Code Prompts Directory:
└── prompts/                    # %APPDATA%\Code\User\prompts
    ├── *.chatmode.md          # Chat modes with tool definitions
    └── *.instruction.md       # General instruction files
```

### ChatMode File Format (.chatmode.md)

```yaml
---
description: "Description of the chat mode"
tools: ["tool1", "tool2", "tool3"]
---

# Chat Mode Instructions

Your chat mode instructions go here...
```

### Instruction File Format (.instruction.md)

```yaml
---
description: "Description of the instruction"
---

# Instruction Content

Your instruction content goes here...
```

## 🧪 Testing

```bash
# Run introspection test
pipenv run python test_introspection.py

# Run full functionality test
pipenv run python test_full_functionality.py

# Test with development script
pipenv run python dev.py test
```

## 🔧 Development

### Project Structure
```
node-manager-mcp/
├── src/mode_manager_mcp/        # Main server code
│   ├── simple_server.py         # MCP server implementation
│   ├── __main__.py              # CLI entry point
│   ├── chatmode_manager.py     # ChatMode file operations
│   ├── instruction_manager.py  # Instruction file operations
│   └── simple_file_ops.py      # File operation utilities
├── docs/                       # Additional documentation
├── test_*.py                   # Test files
├── dev.py                      # Development utilities
├── Pipfile                     # Pipenv dependencies
└── pyproject.toml             # Package configuration
```

### Environment Setup
```bash
# Install pipenv if needed
pip install pipenv

# Create and activate environment
pipenv install

# Run in development mode
pipenv shell
python -m src.mode_manager_mcp
```

## 📋 Configuration

### Environment Variables
- `MCP_CHATMODE_READ_ONLY=true` - Run in read-only mode (no write operations)

### VS Code Settings
The server automatically detects VS Code prompts directory:
- Windows: `%APPDATA%\Code\User\prompts`
- macOS: `~/Library/Application Support/Code/User/prompts`
- Linux: `~/.config/Code/User/prompts`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pipenv run python dev.py test`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Related

- [Mode Manager MCP Library](https://gist.github.com/NiclasOlofsson/0ffc0457b5a1d037766dc4a28c8d3c00) - Official curated library
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [VS Code GitHub Copilot](https://code.visualstudio.com/docs/copilot/overview)
- [VS Code MCP Extension](https://marketplace.visualstudio.com/items?itemName=ModelContextProtocol.mcp)
