# Contributing to Mode Manager MCP

Thank you for your interest in contributing to the Mode Manager MCP Server!

## Development Setup

1. **Install Hatch:**
   ```bash
   pip install hatch
   ```

2. **Clone the repository:**
   ```bash
   git clone https://github.com/NiclasOlofsson/node-manager-mcp.git
   cd node-manager-mcp
   ```

3. **Run tests:**
   ```bash
   hatch run test
   ```

## Development Workflow

### Environment Management

Hatch automatically manages virtual environments for you. No need to create or activate environments manually.

### Running Tests

```bash
# Run all tests
hatch run test

# Run tests with coverage
hatch test --cover

# Run tests in all Python versions (if configured)
hatch test --all
```

### Code Quality

```bash
# Format code with Black
hatch run format

# Check code formatting
hatch run lint

# Run type checking (note: currently has some type annotations to fix)
hatch run typecheck

# Run all quality checks (pre-commit hooks)
hatch run precommit
```

**Note:** Type checking currently reports some annotation issues that need to be addressed in future contributions.

### Building the Project

```bash
# Build wheel and source distribution
hatch build

# Build only wheel
hatch build -t wheel

# Build only source distribution  
hatch build -t sdist
```

### Working with Dependencies

```bash
# Show current dependencies
hatch dep show table

# Install in development mode (automatic with hatch run)
hatch shell  # Enters development environment
```

### Available Scripts

The project defines several convenient scripts in `pyproject.toml`:

- `hatch run test` - Run pytest
- `hatch run lint` - Check code formatting with Black
- `hatch run typecheck` - Run mypy type checking  
- `hatch run format` - Format code with Black
- `hatch run precommit` - Run pre-commit hooks

### Running Individual Commands

```bash
# Run any Python command in the environment
hatch run python -m src.mode_manager_mcp

# Run the server directly for testing
hatch run python -m src.mode_manager_mcp --help

# Enter a shell in the development environment
hatch shell
```

## Development Environment

Hatch automatically creates and manages a virtual environment (`.venv`) in your project directory. This environment:

- Is automatically activated when you run `hatch run` commands
- Contains all project dependencies and development tools
- Is recreated if you delete it or if dependencies change
- Can be entered manually with `hatch shell`

## Quick Reference

| Command | Description |
|---------|-------------|
| `hatch run test` | Run all tests with pytest |
| `hatch run lint` | Check code formatting |
| `hatch run format` | Auto-format code with Black |
| `hatch run typecheck` | Run mypy type checking |
| `hatch build` | Build wheel and source distribution |
| `hatch shell` | Enter development environment |
| `hatch env show` | Show environment information |
| `hatch clean` | Clean build artifacts |

## Code Style

- Follow PEP 8 conventions
- Use type hints where appropriate
- Include docstrings for all public functions and classes
- Keep functions focused and small

## Testing

- Add tests for new functionality
- Ensure all existing tests pass
- Test both success and error cases

## Submitting Changes

1. **Fork the repository**
2. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Run tests**
5. **Commit with clear messages:**
   ```bash
   git commit -m "Add feature: description of changes"
   ```
6. **Push and create a pull request**

## Areas for Contribution

- **Bug fixes** - Check the issue tracker
- **Documentation** - Improve existing docs or add new guides
- **Features** - New chatmode/instruction management features
- **Library expansion** - Add more chatmodes/instructions to the library
- **Testing** - Improve test coverage
- **Performance** - Optimize file operations or network requests

## Code of Conduct

Be respectful, inclusive, and constructive in all interactions.

## Questions?

Feel free to open an issue for questions or discussions!
