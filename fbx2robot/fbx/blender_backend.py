"""Blender backend for FBX extraction.

This module provides functions to extract animation data from FBX files
using Blender's Python API in headless mode.
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Union
import numpy as np

from fbx2robot.config import BLENDER_PATH
from fbx2robot.canonical.schema import CanonicalMotion, MotionFrame


def get_blender_script_path() -> Path:
    """Get path to the Blender extraction script."""
    return Path(__file__).parent / "blender_script.py"


def run_blender_extraction(
    fbx_path: Union[str, Path],
    output_path: Union[str, Path],
    blender_path: Optional[Path] = None,
) -> bool:
    """Run Blender in headless mode to extract FBX data.

    Args:
        fbx_path: Path to input FBX file
        output_path: Path for output JSON file
        blender_path: Optional custom Blender executable path

    Returns:
        True if extraction succeeded
    """
    if blender_path is None:
        blender_path = BLENDER_PATH

    fbx_path = Path(fbx_path).resolve()
    output_path = Path(output_path).resolve()
    script_path = get_blender_script_path().resolve()

    if not fbx_path.exists():
        raise FileNotFoundError(f"FBX file not found: {fbx_path}")

    if not blender_path.exists():
        raise FileNotFoundError(f"Blender not found: {blender_path}")

    # Run Blender in background mode
    cmd = [
        str(blender_path),
        "-b",  # background mode
        "-P",
        str(script_path),  # Python script
        "--",  # separator for script arguments
        str(fbx_path),
        str(output_path),
    ]

    print(f"Running: {' '.join(cmd)}")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=300,  # 5 minute timeout
    )

    if result.returncode != 0:
        print(f"Blender stderr: {result.stderr}")
        print(f"Blender stdout: {result.stdout}")
        return False

    print(result.stdout)
    return output_path.exists()


def json_to_canonical(json_path: Union[str, Path], motion_name: str) -> CanonicalMotion:
    """Convert extracted JSON to CanonicalMotion.

    Args:
        json_path: Path to JSON file from Blender extraction
        motion_name: Name for the motion

    Returns:
        CanonicalMotion object
    """
    json_path = Path(json_path)
    with open(json_path) as f:
        data = json.load(f)

    frames = []
    for frame_data in data["frames"]:
        bone_rotations = {}
        for bone_name, rot in frame_data["bone_rotations"].items():
            # Ensure quaternion is normalized
            rot_array = np.array(rot, dtype=np.float64)
            norm = np.linalg.norm(rot_array)
            if norm > 0:
                rot_array = rot_array / norm
            bone_rotations[bone_name] = rot_array

        root_rot = np.array(frame_data["root_rotation"], dtype=np.float64)
        root_rot = root_rot / np.linalg.norm(root_rot)

        frame = MotionFrame(
            frame_index=frame_data["frame_index"],
            timestamp=frame_data["timestamp"],
            root_position=np.array(frame_data["root_position"], dtype=np.float64),
            root_rotation=root_rot,
            bone_rotations=bone_rotations,
        )
        frames.append(frame)

    return CanonicalMotion(
        name=motion_name,
        source_file=data.get("source_file", str(json_path)),
        fps=data["fps"],
        num_frames=data["num_frames"],
        bone_names=data["bone_names"],
        bone_hierarchy=data["bone_hierarchy"],
        frames=frames,
        source_skeleton_type="mixamo",
    )


def extract_fbx_motion(
    fbx_path: Union[str, Path],
    motion_name: str,
    output_dir: Optional[Union[str, Path]] = None,
    blender_path: Optional[Path] = None,
) -> CanonicalMotion:
    """Extract motion from FBX file and return CanonicalMotion.

    Args:
        fbx_path: Path to FBX file
        motion_name: Name for the motion
        output_dir: Optional directory for intermediate files
        blender_path: Optional custom Blender path

    Returns:
        CanonicalMotion object
    """
    fbx_path = Path(fbx_path)

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="fbx2robot_")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Extract to JSON
    json_path = output_dir / f"{motion_name}_extracted.json"

    success = run_blender_extraction(
        fbx_path=fbx_path,
        output_path=json_path,
        blender_path=blender_path,
    )

    if not success:
        raise RuntimeError(f"Failed to extract FBX: {fbx_path}")

    # Convert to canonical format
    motion = json_to_canonical(json_path, motion_name)

    # Validate
    issues = motion.validate()
    if issues:
        print(f"Warning: Motion validation issues:")
        for issue in issues[:10]:  # Show first 10
            print(f"  - {issue}")

    return motion
