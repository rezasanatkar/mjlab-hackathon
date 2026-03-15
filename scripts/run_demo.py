#!/usr/bin/env python3
"""Run the FBX2Robot demo.

This script launches the interactive demo for judges.
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fbx2robot.llm_demo.demo_runner import main

if __name__ == "__main__":
    main()
