# Mode Manager MCP

Easily manage VS Code `.chatmode.md` and `.instruction.md` files for GitHub Copilot through a Model Context Protocol (MCP) server.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## ✨ What it does

- 📂 **Manage your VS Code prompt files** - Create, edit, and organize chatmodes and instructions
- 📚 **Browse the curated library** - Install popular chatmodes and instructions from the community
- 🔄 **Keep files updated** - Update chatmodes from source while preserving your custom tool settings
- 🛡️ **Safe operations** - Automatic backups before any deletions

## 🚀 Quick Setup

### 1. Install

```bash
git clone https://github.com/NiclasOlofsson/node-manager-mcp.git
cd node-manager-mcp
pipenv install
```

### 2. Test it works

```bash
pipenv run python test_basic.py
```

### 3. Add to VS Code

Copy the example configuration:

```bash
cp mcp-config-example.json .vscode/mcp.json
```

Or manually add to your VS Code MCP settings:

```json
{
  "mcpServers": {
    "mode-manager": {
      "command": "pipenv",
      "args": ["run", "python", "-m", "src.mode_manager_mcp"],
      "cwd": "."
    }
  }
}
```

## � Usage Examples

### Browse the Library
Ask Copilot: *"What chatmodes are available in the library?"*

### Install a Popular Chatmode  
Ask Copilot: *"Install Beast Mode 3.1 from the library"*

### Create Your Own
Ask Copilot: *"Create a new chatmode for API testing"*

### Manage Files
Ask Copilot: *"List my current chatmodes"* or *"Update my chatmode from its source"*

## 📁 Where Files Are Stored

Your prompt files live in VS Code's prompts directory:
- **Windows:** `%APPDATA%\Code\User\prompts`
- **macOS:** `~/Library/Application Support/Code/User/prompts`  
- **Linux:** `~/.config/Code/User/prompts`

## 🤝 Contributing

Want to help improve Mode Manager MCP? Check out [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, coding guidelines, and how to submit changes.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
