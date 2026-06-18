"""Pre-configured tool registry with common tools.

Initializes registry with standard tools for:
- Memory queries
- Shell execution
- HTTP requests
- File operations
- Git commands
"""

from .tools import (
    Tool,
    ToolRegistry,
    create_memory_tool,
    create_shell_tool,
    create_http_tool,
)


def create_default_registry() -> ToolRegistry:
    """Create registry with standard tools.

    Returns: Configured ToolRegistry
    """
    registry = ToolRegistry()

    # Memory tools
    registry.register(create_memory_tool("memory-query"))

    # Execution tools
    registry.register(create_shell_tool("shell-execute"))

    # Network tools
    registry.register(create_http_tool("http-request"))

    # File operation tools
    file_read = Tool(
        name="file-read",
        description="Read file contents",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "encoding": {"type": "string"},
            },
            "required": ["path"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "size_bytes": {"type": "integer"},
            },
        },
    )
    registry.register(file_read)

    file_write = Tool(
        name="file-write",
        description="Write file contents",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
                "mode": {"type": "string"},
            },
            "required": ["path", "content"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "bytes_written": {"type": "integer"},
            },
        },
    )
    registry.register(file_write)

    # Git tools
    git_status = Tool(
        name="git-status",
        description="Get git repository status",
        input_schema={
            "type": "object",
            "properties": {"repo_path": {"type": "string"}},
        },
        output_schema={
            "type": "object",
            "properties": {
                "branch": {"type": "string"},
                "modified_files": {"type": "array"},
                "untracked_files": {"type": "array"},
            },
        },
    )
    registry.register(git_status)

    git_commit = Tool(
        name="git-commit",
        description="Commit changes to repository",
        input_schema={
            "type": "object",
            "properties": {
                "repo_path": {"type": "string"},
                "message": {"type": "string"},
                "files": {"type": "array"},
            },
            "required": ["repo_path", "message"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "commit_hash": {"type": "string"},
                "files_changed": {"type": "integer"},
            },
        },
    )
    registry.register(git_commit)

    return registry
