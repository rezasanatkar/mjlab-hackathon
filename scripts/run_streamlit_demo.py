#!/usr/bin/env python3
"""Launch the Streamlit web demo.

Run with: uv run streamlit run scripts/run_streamlit_demo.py
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Check for streamlit
try:
    import streamlit as st
except ImportError:
    print("Streamlit not installed. Install with: uv pip install streamlit")
    sys.exit(1)

from fbx2robot.llm_demo.streamlit_demo import run_demo

if __name__ == "__main__":
    run_demo()
