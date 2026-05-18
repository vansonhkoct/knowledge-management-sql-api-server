"""Runtime conveniences for the src package."""

from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[1]
_LIBS_PATH = _ROOT / "libs"

if _LIBS_PATH.exists():
	libs_str = str(_LIBS_PATH)
	if libs_str not in sys.path:
		sys.path.insert(0, libs_str)

__all__: list[str] = []
