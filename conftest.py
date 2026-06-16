"""
Pytest configuration — adds src/ to sys.path so tests can import
the package without a full install.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
