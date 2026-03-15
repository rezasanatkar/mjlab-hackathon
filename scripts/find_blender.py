#!/usr/bin/env python3
"""Find and verify Blender installation.

This script searches for Blender in common locations and verifies
it can run in headless mode.
"""

import subprocess
import sys
from pathlib import Path

# Common Blender installation paths on Windows
SEARCH_PATHS = [
    Path(r"C:\Program Files\Blender Foundation"),
    Path(r"C:\Program Files (x86)\Blender Foundation"),
    Path.home() / "AppData" / "Local" / "Blender Foundation",
]


def find_blender_executables() -> list:
    """Find all Blender executables in common locations."""
    found = []

    for base_path in SEARCH_PATHS:
        if not base_path.exists():
            continue

        # Search for blender.exe in subdirectories
        for exe in base_path.rglob("blender.exe"):
            found.append(exe)

    return found


def verify_blender(exe_path: Path) -> dict:
    """Verify Blender executable and get version info."""
    result = {
        "path": str(exe_path),
        "exists": exe_path.exists(),
        "version": None,
        "headless_works": False,
        "error": None,
    }

    if not exe_path.exists():
        result["error"] = "File not found"
        return result

    try:
        # Try to get version
        proc = subprocess.run(
            [str(exe_path), "-b", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if proc.returncode == 0:
            # Parse version from output
            for line in proc.stdout.split("\n"):
                if line.startswith("Blender"):
                    result["version"] = line.strip()
                    break
            result["headless_works"] = True
        else:
            result["error"] = f"Exit code {proc.returncode}: {proc.stderr}"

    except subprocess.TimeoutExpired:
        result["error"] = "Timeout running Blender"
    except Exception as e:
        result["error"] = str(e)

    return result


def main():
    """Main entry point."""
    print("Searching for Blender installations...")
    print()

    executables = find_blender_executables()

    if not executables:
        print("No Blender installations found in common locations.")
        print("\nSearched paths:")
        for p in SEARCH_PATHS:
            print(f"  - {p}")
        print("\nPlease install Blender or specify the path manually.")
        return 1

    print(f"Found {len(executables)} Blender installation(s):")
    print()

    best_version = None
    best_path = None

    for exe in executables:
        info = verify_blender(exe)
        print(f"Path: {info['path']}")
        print(f"  Version: {info['version'] or 'Unknown'}")
        print(f"  Headless mode: {'[OK] Works' if info['headless_works'] else '[X] Failed'}")
        if info["error"]:
            print(f"  Error: {info['error']}")
        print()

        if info["headless_works"]:
            if best_version is None or (
                info["version"] and info["version"] > best_version
            ):
                best_version = info["version"]
                best_path = exe

    if best_path:
        print(f"Recommended Blender: {best_path}")
        print(f"Version: {best_version}")

        # Update config.py suggestion
        print(f"\nTo use this Blender, ensure config.py has:")
        print(f'  BLENDER_PATH = Path(r"{best_path}")')

        return 0
    else:
        print("No working Blender installation found.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
