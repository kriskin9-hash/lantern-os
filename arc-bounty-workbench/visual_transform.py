"""
Visual Transform DSL for ARC Tasks

A domain-specific language for describing and applying visual transformations
to ARC grid tasks. Each transform is a pure function: grid-in, grid-out.
"""

import numpy as np
from typing import Callable, List, Tuple, Optional


Transform = Callable[[np.ndarray], np.ndarray]


# --- Primitive transforms ---

def rotate_90(grid: np.ndarray) -> np.ndarray:
    return np.rot90(grid, k=1)

def rotate_180(grid: np.ndarray) -> np.ndarray:
    return np.rot90(grid, k=2)

def rotate_270(grid: np.ndarray) -> np.ndarray:
    return np.rot90(grid, k=3)

def flip_horizontal(grid: np.ndarray) -> np.ndarray:
    return np.fliplr(grid)

def flip_vertical(grid: np.ndarray) -> np.ndarray:
    return np.flipud(grid)

def transpose(grid: np.ndarray) -> np.ndarray:
    return grid.T

def invert_colors(grid: np.ndarray, max_color: int = 9) -> np.ndarray:
    return max_color - grid

def recolor(grid: np.ndarray, from_color: int, to_color: int) -> np.ndarray:
    result = grid.copy()
    result[result == from_color] = to_color
    return result

def crop(grid: np.ndarray, row_start: int, row_end: int, col_start: int, col_end: int) -> np.ndarray:
    return grid[row_start:row_end, col_start:col_end]

def pad(grid: np.ndarray, pad_width: int, fill_value: int = 0) -> np.ndarray:
    return np.pad(grid, pad_width, constant_values=fill_value)

def tile(grid: np.ndarray, rows: int, cols: int) -> np.ndarray:
    return np.tile(grid, (rows, cols))

def scale_up(grid: np.ndarray, factor: int) -> np.ndarray:
    return np.kron(grid, np.ones((factor, factor), dtype=grid.dtype))


# --- Compound transforms ---

def compose(*transforms: Transform) -> Transform:
    """Compose multiple transforms left to right."""
    def composed(grid: np.ndarray) -> np.ndarray:
        result = grid
        for t in transforms:
            result = t(result)
        return result
    return composed


# --- Transform search space ---

PRIMITIVE_TRANSFORMS = {
    "rotate_90": rotate_90,
    "rotate_180": rotate_180,
    "rotate_270": rotate_270,
    "flip_horizontal": flip_horizontal,
    "flip_vertical": flip_vertical,
    "transpose": transpose,
}


def search_transforms(input_grid: np.ndarray, output_grid: np.ndarray) -> List[str]:
    """Search primitive transforms that map input to output."""
    matches = []
    for name, transform in PRIMITIVE_TRANSFORMS.items():
        try:
            result = transform(input_grid)
            if result.shape == output_grid.shape and np.array_equal(result, output_grid):
                matches.append(name)
        except Exception:
            pass
    return matches


def search_composed_transforms(
    input_grid: np.ndarray,
    output_grid: np.ndarray,
    max_depth: int = 2
) -> List[List[str]]:
    """Search composed transforms up to max_depth that map input to output."""
    matches = []
    names = list(PRIMITIVE_TRANSFORMS.keys())
    transforms = list(PRIMITIVE_TRANSFORMS.values())

    if max_depth >= 1:
        for name, t in zip(names, transforms):
            try:
                result = t(input_grid)
                if result.shape == output_grid.shape and np.array_equal(result, output_grid):
                    matches.append([name])
            except Exception:
                pass

    if max_depth >= 2:
        for i, (n1, t1) in enumerate(zip(names, transforms)):
            for n2, t2 in zip(names, transforms):
                try:
                    result = t2(t1(input_grid))
                    if result.shape == output_grid.shape and np.array_equal(result, output_grid):
                        matches.append([n1, n2])
                except Exception:
                    pass

    return matches


if __name__ == "__main__":
    grid = np.array([[1, 2], [3, 4]])
    print("Original:", grid)
    print("Rotate 90:", rotate_90(grid))
    print("Flip H:", flip_horizontal(grid))
    print("Search:", search_transforms(grid, rotate_90(grid)))
