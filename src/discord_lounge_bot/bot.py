"""
Lantern OS Discord Bot v1 -- backward-compat wrapper
The canonical implementation is bot_v2.py (slash + prefix commands + Three Doors).
"""
import sys
from pathlib import Path

# Ensure bot_v2 is importable from this directory
sys.path.insert(0, str(Path(__file__).parent))
from bot_v2 import main  # noqa: E402

if __name__ == "__main__":
    main()
