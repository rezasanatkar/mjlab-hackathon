#!/usr/bin/env python3
"""Process FBX file through the FBX2Robot pipeline.

Usage:
    python scripts/process_fbx.py --input data/motions/bow_greeting/source.fbx \
                                   --output-dir data/motions/bow_greeting \
                                   --motion-name bow_greeting
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fbx2robot.cli import main

if __name__ == "__main__":
    sys.exit(main())
