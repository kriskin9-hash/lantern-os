"""
ARC Task Loader

Loads and preprocesses ARC tasks for local evaluation.
Supports both ARC-AGI-2 (static) and ARC-AGI-3 (interactive) task formats.
"""

import json
from pathlib import Path
from typing import Dict, List, Any
import numpy as np


class ARCTaskLoader:
    """Load and validate ARC tasks from official dataset format."""
    
    def __init__(self, data_path: str):
        self.data_path = Path(data_path)
        self.tasks = {}
        
    def load_task(self, task_id: str) -> Dict[str, Any]:
        """Load a single task by ID."""
        task_file = self.data_path / f"{task_id}.json"
        if not task_file.exists():
            raise FileNotFoundError(f"Task {task_id} not found")
        
        with open(task_file, 'r') as f:
            task = json.load(f)
        
        self.tasks[task_id] = task
        return task
    
    def load_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Load all tasks from data directory."""
        for task_file in self.data_path.glob("*.json"):
            task_id = task_file.stem
            self.tasks[task_id] = self.load_task(task_id)
        
        return self.tasks
    
    def validate_task(self, task: Dict[str, Any]) -> bool:
        """Validate task has required fields."""
        required_fields = ['train', 'test']
        for field in required_fields:
            if field not in task:
                return False
        
        # Validate train/test examples
        for example in task['train']:
            if 'input' not in example or 'output' not in example:
                return False
        
        for example in task['test']:
            if 'input' not in example:
                return False
        
        return True
    
    def get_task_input(self, task_id: str, example_idx: int = 0) -> np.ndarray:
        """Get input grid for a task example."""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not loaded")
        
        if example_idx >= len(task['train']):
            raise ValueError(f"Example index {example_idx} out of range")
        
        return np.array(task['train'][example_idx]['input'])
    
    def get_task_output(self, task_id: str, example_idx: int = 0) -> np.ndarray:
        """Get output grid for a task example."""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not loaded")
        
        if example_idx >= len(task['train']):
            raise ValueError(f"Example index {example_idx} out of range")
        
        return np.array(task['train'][example_idx]['output'])
    
    def get_test_input(self, task_id: str, test_idx: int = 0) -> np.ndarray:
        """Get test input grid for a task."""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not loaded")
        
        if test_idx >= len(task['test']):
            raise ValueError(f"Test index {test_idx} out of range")
        
        return np.array(task['test'][test_idx]['input'])


# Stub for immediate use
if __name__ == "__main__":
    # Example usage stub
    loader = ARCTaskLoader("data/arc-bounty/tasks")
    print("ARC Task Loader initialized")
    print("Load tasks with: loader.load_all_tasks()")
