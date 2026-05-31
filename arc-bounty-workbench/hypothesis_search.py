"""
ARC Hypothesis Search

Program synthesis search over visual transformation strategies.
Implements local-first search with deterministic seeds and receipt tracking.
"""

import numpy as np
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass
import copy


@dataclass
class TransformOperation:
    """A single visual transform operation."""
    name: str
    params: Dict[str, Any]
    apply: Callable[[np.ndarray], np.ndarray]


@dataclass
class Hypothesis:
    """A candidate solution hypothesis."""
    operations: List[TransformOperation]
    confidence: float = 0.0
    test_cases_passed: int = 0
    
    def apply(self, grid: np.ndarray) -> np.ndarray:
        """Apply all operations in sequence."""
        result = grid.copy()
        for op in self.operations:
            result = op.apply(result)
        return result


class HypothesisSearch:
    """
    Search over program space for ARC task solutions.
    
    Implements local-first, deterministic search with:
    - Explicit operation primitives (no learned heuristics)
    - Train-set validation before test prediction
    - Reproducible results via seed control
    """
    
    def __init__(self, seed: int = 42, max_depth: int = 3):
        self.seed = seed
        self.max_depth = max_depth
        self.np_rng = np.random.RandomState(seed)
        self.primitives = self._define_primitives()
        self.hypotheses: List[Hypothesis] = []
        
    def _define_primitives(self) -> List[TransformOperation]:
        """Define basic visual transformation primitives."""
        primitives = []
        
        # Color mapping operations
        def color_map(grid: np.ndarray, mapping: Dict[int, int]) -> np.ndarray:
            result = grid.copy()
            for old, new in mapping.items():
                result[grid == old] = new
            return result
        
        # Rotation
        def rotate(grid: np.ndarray, k: int = 1) -> np.ndarray:
            return np.rot90(grid, k=k)
        
        # Flip
        def flip_horizontal(grid: np.ndarray) -> np.ndarray:
            return np.fliplr(grid)
        
        def flip_vertical(grid: np.ndarray) -> np.ndarray:
            return np.flipud(grid)
        
        # Crop/pad to fixed size
        def crop_to_content(grid: np.ndarray) -> np.ndarray:
            """Crop to bounding box of non-zero content."""
            rows = np.any(grid != 0, axis=1)
            cols = np.any(grid != 0, axis=0)
            if not np.any(rows) or not np.any(cols):
                return grid
            rmin, rmax = np.where(rows)[0][[0, -1]]
            cmin, cmax = np.where(cols)[0][[0, -1]]
            return grid[rmin:rmax+1, cmin:cmax+1]
        
        # Add primitives
        primitives.append(TransformOperation(
            "rotate_90", {"k": 1}, 
            lambda g: rotate(g, 1)
        ))
        primitives.append(TransformOperation(
            "rotate_180", {"k": 2}, 
            lambda g: rotate(g, 2)
        ))
        primitives.append(TransformOperation(
            "flip_horizontal", {}, 
            flip_horizontal
        ))
        primitives.append(TransformOperation(
            "flip_vertical", {}, 
            flip_vertical
        ))
        primitives.append(TransformOperation(
            "crop_to_content", {}, 
            crop_to_content
        ))
        
        # Color identity (pass-through)
        primitives.append(TransformOperation(
            "identity", {}, 
            lambda g: g.copy()
        ))
        
        return primitives
    
    def _generate_candidate(self, depth: int = 1) -> Hypothesis:
        """Generate a random candidate hypothesis."""
        ops = []
        for _ in range(depth):
            op_idx = self.np_rng.randint(0, len(self.primitives))
            ops.append(copy.deepcopy(self.primitives[op_idx]))
        return Hypothesis(operations=ops)
    
    def search(self, 
               train_examples: List[Dict[str, np.ndarray]], 
               max_candidates: int = 1000) -> Optional[Hypothesis]:
        """
        Search for hypothesis that fits all training examples.
        
        Args:
            train_examples: List of {'input': grid, 'output': grid}
            max_candidates: Maximum hypotheses to try
            
        Returns:
            Best hypothesis or None if no solution found
        """
        best_hypothesis = None
        best_score = 0
        
        for i in range(max_candidates):
            # Generate candidate
            depth = self.np_rng.randint(1, self.max_depth + 1)
            candidate = self._generate_candidate(depth)
            
            # Test on all training examples
            score = 0
            all_pass = True
            
            for example in train_examples:
                input_grid = example['input']
                expected_output = example['output']
                
                try:
                    predicted = candidate.apply(input_grid)
                    
                    # Exact match check
                    if predicted.shape == expected_output.shape:
                        matches = np.sum(predicted == expected_output)
                        total = expected_output.size
                        score += matches / total
                        
                        if matches != total:
                            all_pass = False
                    else:
                        all_pass = False
                        
                except Exception as e:
                    all_pass = False
                    continue
            
            # Normalize score
            if train_examples:
                score /= len(train_examples)
            
            candidate.confidence = score
            candidate.test_cases_passed = int(all_pass)
            self.hypotheses.append(candidate)
            
            # Track best
            if score > best_score:
                best_score = score
                best_hypothesis = candidate
            
            # Early exit if perfect match
            if all_pass and score >= 1.0:
                break
        
        return best_hypothesis
    
    def predict(self, test_input: np.ndarray, hypothesis: Hypothesis) -> np.ndarray:
        """Apply best hypothesis to test input."""
        return hypothesis.apply(test_input)
    
    def get_search_stats(self) -> Dict[str, Any]:
        """Get statistics from search process."""
        if not self.hypotheses:
            return {"total_candidates": 0, "perfect_matches": 0}
        
        perfect_matches = sum(1 for h in self.hypotheses if h.test_cases_passed > 0)
        confidences = [h.confidence for h in self.hypotheses]
        
        return {
            "total_candidates": len(self.hypotheses),
            "perfect_matches": perfect_matches,
            "max_confidence": max(confidences),
            "mean_confidence": np.mean(confidences),
            "seed": self.seed
        }


# Local ARC task simulator for testing
class LocalARCSimulator:
    """Simulate ARC-style tasks without internet access."""
    
    def __init__(self):
        self.tasks = self._create_test_tasks()
    
    def _create_test_tasks(self) -> Dict[str, Any]:
        """Create simple test tasks for local validation."""
        tasks = {}
        
        # Task 1: Simple rotation
        tasks["test_rotate_90"] = {
            "train": [
                {
                    "input": np.array([[1, 0], [0, 0]]),
                    "output": np.array([[0, 1], [0, 0]])  # rotated 90
                }
            ],
            "test": [
                {"input": np.array([[0, 1], [0, 0]])}
            ]
        }
        
        # Task 2: Flip horizontal
        tasks["test_flip_h"] = {
            "train": [
                {
                    "input": np.array([[1, 2, 3]]),
                    "output": np.array([[3, 2, 1]])
                }
            ],
            "test": [
                {"input": np.array([[4, 5, 6]])}
            ]
        }
        
        return tasks
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """Get a test task by ID."""
        return self.tasks.get(task_id)


if __name__ == "__main__":
    # Test stub - run local validation
    print("=== ARC Hypothesis Search Test ===")
    
    simulator = LocalARCSimulator()
    task = simulator.get_task("test_rotate_90")
    
    if task:
        print(f"Task loaded: {len(task['train'])} train examples")
        
        # Run search
        search = HypothesisSearch(seed=42, max_depth=2)
        best = search.search(task['train'], max_candidates=100)
        
        if best:
            print(f"Best hypothesis found: {len(best.operations)} operations")
            print(f"Confidence: {best.confidence:.2%}")
            
            # Test prediction
            test_input = task['test'][0]['input']
            predicted = search.predict(test_input, best)
            print(f"Test prediction shape: {predicted.shape}")
        else:
            print("No hypothesis found")
        
        stats = search.get_search_stats()
        print(f"Search stats: {stats}")
    
    print("\n=== Test Complete ===")
    print("Ready for ARC dataset integration")
