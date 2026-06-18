"""LANTERN-TOOLS: Unified execution layer (MCP-compatible).

Wraps existing REST endpoints and tools as composable Tool objects
with consistent input/output contracts and confidence scoring.

Implements the Act stage of the Convergence Loop.
Every tool returns {success, output, confidence} for grounded reasoning.

Reference: CONVERGANCE-SIGMA0-BRIEFING.md, RESEARCH-CANON.md [05]
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Callable, List
from enum import Enum
import json


class ToolStatus(str, Enum):
    """Execution outcome."""
    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class ToolInput:
    """Validated tool input."""
    parameters: Dict[str, Any]
    schema: Optional[Dict[str, Any]] = None


@dataclass
class ToolOutput:
    """Structured tool execution result."""
    status: ToolStatus
    data: Dict[str, Any]  # Actual output
    confidence: float  # 0.0-1.0: how much to trust this output
    error: Optional[str] = None
    execution_time_ms: float = 0.0

    def is_success(self) -> bool:
        """True if execution succeeded."""
        return self.status == ToolStatus.SUCCESS

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "status": self.status.value,
            "data": self.data,
            "confidence": self.confidence,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
        }


@dataclass
class ToolSchema:
    """JSON Schema definitions for tool I/O."""
    input_schema: Dict[str, Any] = field(default_factory=lambda: {"type": "object"})
    output_schema: Dict[str, Any] = field(default_factory=lambda: {"type": "object"})

    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input against schema (basic check)."""
        if not isinstance(data, dict):
            return False
        # In production, use jsonschema library for full validation
        return True

    def validate_output(self, data: Dict[str, Any]) -> bool:
        """Validate output against schema (basic check)."""
        return isinstance(data, dict)


class Tool:
    """Executable capability with standardized I/O contract.

    Every tool call returns {status, data, confidence, error}
    enabling downstream reasoning to score trustworthiness.
    """

    def __init__(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        output_schema: Dict[str, Any],
        executor: Optional[Callable] = None,
    ):
        """Initialize tool.

        Args:
            name: Unique tool identifier
            description: Human-readable purpose
            input_schema: JSON Schema for inputs
            output_schema: JSON Schema for outputs
            executor: Callable that implements the tool (for async execution)
        """
        self.name = name
        self.description = description
        self.schema = ToolSchema(input_schema, output_schema)
        self.executor = executor
        self.call_count = 0
        self.success_count = 0

    async def call(self, input_data: Dict[str, Any]) -> ToolOutput:
        """Execute the tool with given input.

        Args:
            input_data: Parameters for the tool

        Returns: ToolOutput with status, data, and confidence
        """
        self.call_count += 1

        # Validate input
        if not self.schema.validate_input(input_data):
            return ToolOutput(
                status=ToolStatus.ERROR,
                data={},
                confidence=0.0,
                error="Invalid input format",
            )

        try:
            # Execute tool
            if self.executor:
                output = await self.executor(input_data)
            else:
                output = await self._default_execute(input_data)

            # Validate output
            if not self.schema.validate_output(output):
                return ToolOutput(
                    status=ToolStatus.ERROR,
                    data=output,
                    confidence=0.5,
                    error="Output validation failed",
                )

            # Success case
            self.success_count += 1
            return ToolOutput(
                status=ToolStatus.SUCCESS,
                data=output,
                confidence=self.get_reliability(),
            )

        except Exception as e:
            return ToolOutput(
                status=ToolStatus.ERROR,
                data={},
                confidence=0.0,
                error=str(e),
            )

    async def _default_execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Default implementation (can be overridden)."""
        return input_data

    def get_reliability(self) -> float:
        """Estimate tool reliability based on history.

        Returns: Confidence based on success rate
        """
        if self.call_count == 0:
            return 0.8  # New tool: moderate confidence
        return min(1.0, 0.5 + (self.success_count / self.call_count) * 0.5)

    def statistics(self) -> Dict[str, Any]:
        """Get tool execution statistics."""
        return {
            "name": self.name,
            "total_calls": self.call_count,
            "successful_calls": self.success_count,
            "success_rate": (
                self.success_count / self.call_count if self.call_count > 0 else 0.0
            ),
            "estimated_reliability": self.get_reliability(),
        }


class ToolRegistry:
    """Registry of available tools."""

    def __init__(self):
        """Initialize empty tool registry."""
        self.tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool.

        Args:
            tool: Tool object to register
        """
        self.tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        """Get tool by name.

        Args:
            name: Tool identifier

        Returns: Tool object or None
        """
        return self.tools.get(name)

    async def call(self, name: str, input_data: Dict[str, Any]) -> ToolOutput:
        """Call a tool by name.

        Args:
            name: Tool identifier
            input_data: Tool parameters

        Returns: ToolOutput
        """
        tool = self.get(name)
        if not tool:
            return ToolOutput(
                status=ToolStatus.ERROR,
                data={},
                confidence=0.0,
                error=f"Tool '{name}' not found",
            )
        return await tool.call(input_data)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.schema.input_schema,
                "output_schema": tool.schema.output_schema,
            }
            for tool in self.tools.values()
        ]

    def statistics(self) -> Dict[str, Any]:
        """Get statistics for all tools."""
        return {
            "total_tools": len(self.tools),
            "tools": [tool.statistics() for tool in self.tools.values()],
            "aggregate_success_rate": (
                sum(t.success_count for t in self.tools.values())
                / max(1, sum(t.call_count for t in self.tools.values()))
            ),
        }


# Global tool registry instance
_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get or create global tool registry."""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry


def reset_tool_registry() -> None:
    """Reset registry (for testing)."""
    global _tool_registry
    _tool_registry = None


# Standard tool factories for common tasks
def create_shell_tool(name: str = "shell-execute") -> Tool:
    """Factory for shell execution tool."""
    return Tool(
        name=name,
        description="Execute shell commands",
        input_schema={
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "timeout": {"type": "number"},
            },
            "required": ["command"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "stdout": {"type": "string"},
                "stderr": {"type": "string"},
                "exit_code": {"type": "integer"},
            },
        },
    )


def create_memory_tool(name: str = "memory-query") -> Tool:
    """Factory for memory query tool."""
    return Tool(
        name=name,
        description="Query persistent memory",
        input_schema={
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "min_confidence": {"type": "number"},
                "limit": {"type": "integer"},
            },
            "required": ["pattern"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "results": {
                    "type": "array",
                    "items": {"type": "object"},
                },
            },
        },
    )


def create_http_tool(name: str = "http-request") -> Tool:
    """Factory for HTTP request tool."""
    return Tool(
        name=name,
        description="Make HTTP requests",
        input_schema={
            "type": "object",
            "properties": {
                "method": {"type": "string"},
                "url": {"type": "string"},
                "headers": {"type": "object"},
                "body": {"type": "object"},
                "timeout": {"type": "number"},
            },
            "required": ["method", "url"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "status_code": {"type": "integer"},
                "headers": {"type": "object"},
                "body": {"type": "object"},
            },
        },
    )
