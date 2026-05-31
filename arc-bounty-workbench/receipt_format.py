"""
ARC Experiment Receipt Format

Defines the receipt format for recording experiment runs,
ensuring reproducibility and auditability.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import hashlib


class ARCExperimentReceipt:
    """Receipt for ARC experiment runs."""
    
    def __init__(self, experiment_id: str):
        self.experiment_id = experiment_id
        self.timestamp = datetime.utcnow().isoformat()
        self.data = {
            "experiment_id": experiment_id,
            "timestamp": self.timestamp,
            "method": None,
            "seed": None,
            "tasks": [],
            "results": {},
            "parameters": {},
            "environment": {},
            "receipt_hash": None
        }
    
    def set_method(self, method_name: str, method_version: str = "1.0"):
        """Set the method used."""
        self.data["method"] = {
            "name": method_name,
            "version": method_version
        }
    
    def set_seed(self, seed: int):
        """Set random seed for reproducibility."""
        self.data["seed"] = seed
    
    def add_task(self, task_id: str, task_hash: str):
        """Add a task to the receipt."""
        self.data["tasks"].append({
            "task_id": task_id,
            "task_hash": task_hash
        })
    
    def set_parameter(self, key: str, value: Any):
        """Set a method parameter."""
        self.data["parameters"][key] = value
    
    def set_environment(self, key: str, value: Any):
        """Set environment variable."""
        self.data["environment"][key] = value
    
    def record_result(self, task_id: str, 
                     predicted_output: Any, 
                     actual_output: Optional[Any] = None,
                     accuracy: Optional[float] = None,
                     runtime_ms: Optional[float] = None):
        """Record result for a task."""
        if task_id not in self.data["results"]:
            self.data["results"][task_id] = {}
        
        self.data["results"][task_id]["predicted"] = str(predicted_output)
        if actual_output is not None:
            self.data["results"][task_id]["actual"] = str(actual_output)
        if accuracy is not None:
            self.data["results"][task_id]["accuracy"] = accuracy
        if runtime_ms is not None:
            self.data["results"][task_id]["runtime_ms"] = runtime_ms
    
    def compute_hash(self) -> str:
        """Compute receipt hash for integrity."""
        receipt_str = json.dumps(self.data, sort_keys=True)
        return hashlib.sha256(receipt_str.encode()).hexdigest()
    
    def finalize(self) -> str:
        """Finalize receipt and return hash."""
        self.data["receipt_hash"] = self.compute_hash()
        return self.data["receipt_hash"]
    
    def save(self, output_path: str):
        """Save receipt to file."""
        self.finalize()
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(self.data, f, indent=2)
        
        return str(output_file)
    
    def load(self, input_path: str):
        """Load receipt from file."""
        input_file = Path(input_path)
        with open(input_file, 'r') as f:
            self.data = json.load(f)
        
        # Verify hash
        computed_hash = self.compute_hash()
        if computed_hash != self.data.get("receipt_hash"):
            raise ValueError("Receipt hash mismatch - file may be corrupted")


# Stub for immediate use
if __name__ == "__main__":
    # Example usage stub
    receipt = ARCExperimentReceipt("test-run-001")
    receipt.set_method("curiosity-policy")
    receipt.set_seed(42)
    print("ARC Experiment Receipt initialized")
    print("Save receipt with: receipt.save('experiments/receipt.json')")
