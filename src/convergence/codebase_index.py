"""LANTERN-OBSERVATORY: Repository structure and relationship understanding.

Auto-generates architecture maps, dependency graphs, and module indexes
to enable intelligent navigation and pattern detection.

Implements the Observatory component that provides contextual understanding
of the codebase to reasoning engines (dream-chat, router, etc.).
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class Module:
    """Code module with relationships and characteristics."""
    path: str  # Relative path: src/convergence/kernel.py
    name: str  # Base name: kernel
    module_type: str  # Type: convergence, test, tool, route, etc.
    description: Optional[str] = None
    imports: List[str] = None  # Other modules it imports
    exports: List[str] = None  # What it exports
    purpose: Optional[str] = None  # What it does
    size_lines: int = 0

    def __post_init__(self):
        if self.imports is None:
            self.imports = []
        if self.exports is None:
            self.exports = []


@dataclass
class Architecture:
    """Architecture component grouping related modules."""
    name: str  # LANTERN-KERNEL, LANTERN-MEMORY, etc.
    description: str
    modules: List[str] = None  # Module paths
    layer: str = "core"  # core, service, tool, test
    dependencies: List[str] = None  # Other components it depends on

    def __post_init__(self):
        if self.modules is None:
            self.modules = []
        if self.dependencies is None:
            self.dependencies = []


class CodebaseIndex:
    """Analyzes and indexes repository structure."""

    def __init__(self, repo_root: str):
        """Initialize with repository root path."""
        self.repo_root = Path(repo_root)
        self.modules: Dict[str, Module] = {}
        self.architectures: Dict[str, Architecture] = {}
        self.patterns: Dict[str, Any] = {}
        self._initialize_architectures()

    def _initialize_architectures(self) -> None:
        """Define known architecture components."""
        self.architectures = {
            "LANTERN-KERNEL": Architecture(
                name="LANTERN-KERNEL",
                description="Core orchestration loop (Observe→Remember→Reason→Act→Verify→Converge)",
                layer="core",
                modules=["src/convergence/kernel.py"],
                dependencies=["LANTERN-MEMORY", "LANTERN-TOOLS"],
            ),
            "LANTERN-MEMORY": Architecture(
                name="LANTERN-MEMORY",
                description="Append-only persistent knowledge (JSONL + CSF)",
                layer="core",
                modules=["src/convergence/objects.py"],
                dependencies=[],
            ),
            "LANTERN-TOOLS": Architecture(
                name="LANTERN-TOOLS",
                description="Unified execution layer (MCP-compatible)",
                layer="core",
                modules=["src/convergence/tools.py"],
                dependencies=[],
            ),
            "LANTERN-GRAPH": Architecture(
                name="LANTERN-GRAPH",
                description="Knowledge relationships (GraphRAG-based)",
                layer="core",
                modules=["src/convergence/graph.py"],
                dependencies=["LANTERN-MEMORY"],
            ),
            "LANTERN-VERIFY": Architecture(
                name="LANTERN-VERIFY",
                description="Reality validation (tests, benchmarks, evidence)",
                layer="core",
                modules=["src/convergence/verify.py", "src/cio_sde/surprise.py"],
                dependencies=["LANTERN-KERNEL"],
            ),
            "LANTERN-CONVERGENCE": Architecture(
                name="LANTERN-CONVERGENCE",
                description="Pattern extraction and self-improvement",
                layer="core",
                modules=["src/convergence/convergence.py"],
                dependencies=["LANTERN-MEMORY", "LANTERN-KERNEL"],
            ),
            "LANTERN-CODER": Architecture(
                name="LANTERN-CODER",
                description="Coding specialization (task-based)",
                layer="service",
                modules=["apps/lantern-garage/lib/dream-chat.js"],
                dependencies=["LANTERN-KERNEL", "LANTERN-TOOLS"],
            ),
            "LANTERN-DREAM": Architecture(
                name="LANTERN-DREAM",
                description="Exploration mode (high-creativity reasoning)",
                layer="service",
                modules=["apps/lantern-garage/public/dream-chat.html"],
                dependencies=["LANTERN-KERNEL"],
            ),
            "LANTERN-OBSERVATORY": Architecture(
                name="LANTERN-OBSERVATORY",
                description="Repository and system understanding",
                layer="service",
                modules=["src/convergence/codebase_index.py"],
                dependencies=[],
            ),
            "LANTERN-SANDBOX": Architecture(
                name="LANTERN-SANDBOX",
                description="Safe isolated execution (worktrees, snapshots)",
                layer="tool",
                modules=[],
                dependencies=[],
            ),
            "LANTERN-LOCAL": Architecture(
                name="LANTERN-LOCAL",
                description="User sovereignty (offline-first)",
                layer="foundation",
                modules=[],
                dependencies=[],
            ),
        }

    def scan_repository(self) -> Dict[str, Module]:
        """Scan repository and index all modules."""
        patterns_found = self._identify_patterns()
        self.patterns = patterns_found

        # Index core Convergence modules
        convergence_path = self.repo_root / "src" / "convergence"
        if convergence_path.exists():
            for file in convergence_path.glob("*.py"):
                self._index_file(file)

        # Index tests
        tests_path = self.repo_root / "tests"
        if tests_path.exists():
            for file in tests_path.glob("test_convergence*.py"):
                self._index_file(file)

        # Index routes
        routes_path = self.repo_root / "apps" / "lantern-garage" / "routes"
        if routes_path.exists():
            for file in routes_path.glob("*.js"):
                self._index_file(file)

        # Index main components
        lib_path = self.repo_root / "apps" / "lantern-garage" / "lib"
        if lib_path.exists():
            for file in lib_path.glob("*.js"):
                self._index_file(file)

        return self.modules

    def _index_file(self, filepath: Path) -> None:
        """Index a single file."""
        try:
            rel_path = str(filepath.relative_to(self.repo_root))
            name = filepath.stem

            # Determine module type
            if "test" in rel_path:
                module_type = "test"
            elif "convergence" in rel_path:
                module_type = "convergence"
            elif "routes" in rel_path:
                module_type = "route"
            elif "lib" in rel_path:
                module_type = "library"
            else:
                module_type = "other"

            # Read file content for analysis
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    size = len(content.split("\n"))
            except Exception:
                content = ""
                size = 0

            # Parse imports (basic)
            imports = self._extract_imports(content, filepath.suffix)

            # Create module
            module = Module(
                path=rel_path,
                name=name,
                module_type=module_type,
                imports=imports,
                size_lines=size,
            )

            # Set description based on docstring
            if filepath.suffix == ".py":
                module.description = self._extract_docstring(content)

            self.modules[rel_path] = module

        except Exception as e:
            print(f"Error indexing {filepath}: {e}")

    def _extract_imports(self, content: str, suffix: str) -> List[str]:
        """Extract module imports."""
        imports = []
        lines = content.split("\n")

        if suffix == ".py":
            for line in lines[:50]:  # Check first 50 lines
                if line.startswith("import ") or line.startswith("from "):
                    imports.append(line.strip())

        elif suffix == ".js":
            for line in lines[:50]:
                if "require(" in line or "import " in line:
                    imports.append(line.strip())

        return imports[:10]  # Limit to first 10

    def _extract_docstring(self, content: str) -> Optional[str]:
        """Extract module docstring."""
        lines = content.split("\n")
        if not lines:
            return None

        # Check if first line contains opening """
        if '"""' in lines[0]:
            # Count occurrences - if 2, it's a single-line docstring
            count = lines[0].count('"""')
            if count == 2:
                # Single-line docstring like """docstring."""
                return lines[0].replace('"""', "").strip()
            else:
                # Multi-line docstring, find closing """
                for i, line in enumerate(lines[1:], 1):
                    if '"""' in line:
                        # Return everything between the triple quotes
                        docstring = "\n".join(lines[0:i+1])
                        docstring = docstring.replace('"""', "").strip()
                        return docstring
        return None

    def _identify_patterns(self) -> Dict[str, Any]:
        """Identify architectural patterns in codebase."""
        return {
            "convergence_loop": {
                "description": "Six-stage loop: Observe→Remember→Reason→Act→Verify→Converge",
                "implemented_in": ["src/convergence/kernel.py"],
            },
            "append_only_persistence": {
                "description": "JSONL logs for immutable knowledge storage",
                "locations": ["data/"],
            },
            "monoworkstream": {
                "description": "One PR lane per agent at a time",
                "enforced_by": ["git hooks"],
            },
            "convergence_records": {
                "description": "Structured reasoning: hypothesis + evidence + result + confidence",
                "defined_in": ["src/convergence/objects.py"],
            },
        }

    def to_json(self) -> Dict[str, Any]:
        """Export index as JSON."""
        return {
            "modules": {
                path: {
                    "name": mod.name,
                    "type": mod.module_type,
                    "description": mod.description,
                    "imports": mod.imports[:5],  # First 5
                    "size_lines": mod.size_lines,
                }
                for path, mod in self.modules.items()
            },
            "architectures": {
                name: {
                    "description": arch.description,
                    "layer": arch.layer,
                    "modules": arch.modules,
                    "dependencies": arch.dependencies,
                }
                for name, arch in self.architectures.items()
            },
            "patterns": self.patterns,
            "statistics": {
                "total_modules": len(self.modules),
                "total_architectures": len(self.architectures),
                "total_lines": sum(m.size_lines for m in self.modules.values()),
            },
        }

    def save_index(self, output_path: str = "src/convergence/codebase_index.json") -> None:
        """Save index to JSON file."""
        output_file = self.repo_root / output_path
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(self.to_json(), f, indent=2)

        print(f"Codebase index saved to {output_path}")
