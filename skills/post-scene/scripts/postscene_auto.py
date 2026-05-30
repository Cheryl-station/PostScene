#!/usr/bin/env python3
"""Recommend, lint, and convert a PostScene workflow in one command."""

from pathlib import Path
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from post_scene.auto import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
