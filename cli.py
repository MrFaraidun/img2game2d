#!/usr/bin/env python3
"""Root CLI entrypoint for img2game2d."""
import sys
from pathlib import Path

# Add project root and forge to sys.path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "forge"))

from forge.cli import main

if __name__ == "__main__":
    sys.exit(main())
