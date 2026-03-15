#!/usr/bin/env python3
"""Process all FBX files in the Mixamo directory.

This script runs the full pipeline on all available FBX motion files.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fbx2robot.pipeline import process_all_motions
from fbx2robot.config import MIXAMO_DIR


def main():
    """Run processing on all motions."""
    print("=" * 60)
    print("FBX2Robot Motion Suite Processor")
    print("=" * 60)
    print(f"\nMixamo directory: {MIXAMO_DIR}")

    if not MIXAMO_DIR.exists():
        print(f"Error: Mixamo directory not found: {MIXAMO_DIR}")
        return 1

    fbx_files = list(MIXAMO_DIR.glob("*.fbx"))
    print(f"Found {len(fbx_files)} FBX files:\n")
    for f in fbx_files:
        print(f"  - {f.name}")

    print("\n" + "=" * 60)
    print("Starting processing...")
    print("=" * 60)

    results = process_all_motions()

    # Final summary
    print("\n" + "=" * 60)
    print("Final Results")
    print("=" * 60)

    successes = [name for name, r in results.items() if r.success]
    failures = [name for name, r in results.items() if not r.success]

    print(f"\nSuccessful: {len(successes)}")
    for name in successes:
        result = results[name]
        print(f"  ✓ {name}")
        print(f"      CSV: {result.csv_path}")

    if failures:
        print(f"\nFailed: {len(failures)}")
        for name in failures:
            result = results[name]
            print(f"  ✗ {name}")
            print(f"      Error: {result.error}")

    return 0 if len(failures) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
