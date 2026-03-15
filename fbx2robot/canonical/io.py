"""I/O utilities for canonical motion representation."""

import json
from pathlib import Path
from typing import Union
import numpy as np

from fbx2robot.canonical.schema import CanonicalMotion, MotionFrame


def save_canonical(motion: CanonicalMotion, output_path: Union[str, Path]) -> Path:
    """Save canonical motion to NPZ format.

    Args:
        motion: Canonical motion to save
        output_path: Path to save to (will add .npz extension if missing)

    Returns:
        Path to saved file
    """
    output_path = Path(output_path)
    if output_path.suffix != ".npz":
        output_path = output_path.with_suffix(".npz")

    # Prepare arrays
    root_positions = np.array([f.root_position for f in motion.frames])
    root_rotations = np.array([f.root_rotation for f in motion.frames])

    # Prepare bone rotations as a dict of arrays
    bone_rotation_arrays = {}
    for bone_name in motion.bone_names:
        bone_rotation_arrays[f"bone_{bone_name}"] = motion.get_bone_trajectory(
            bone_name
        )

    # Prepare metadata as JSON string
    metadata = {
        "name": motion.name,
        "source_file": motion.source_file,
        "fps": motion.fps,
        "num_frames": motion.num_frames,
        "duration": motion.duration,
        "bone_names": motion.bone_names,
        "bone_hierarchy": motion.bone_hierarchy,
        "source_skeleton_type": motion.source_skeleton_type,
    }

    # Save
    np.savez(
        output_path,
        root_positions=root_positions,
        root_rotations=root_rotations,
        metadata=json.dumps(metadata),
        **bone_rotation_arrays,
    )

    return output_path


def load_canonical(input_path: Union[str, Path]) -> CanonicalMotion:
    """Load canonical motion from NPZ format.

    Args:
        input_path: Path to NPZ file

    Returns:
        Loaded CanonicalMotion
    """
    input_path = Path(input_path)
    data = np.load(input_path, allow_pickle=True)

    # Load metadata
    metadata = json.loads(str(data["metadata"]))

    # Reconstruct frames
    root_positions = data["root_positions"]
    root_rotations = data["root_rotations"]
    bone_names = metadata["bone_names"]

    frames = []
    for i in range(len(root_positions)):
        bone_rotations = {}
        for bone_name in bone_names:
            key = f"bone_{bone_name}"
            if key in data:
                bone_rotations[bone_name] = data[key][i]

        frame = MotionFrame(
            frame_index=i,
            timestamp=i / metadata["fps"],
            root_position=root_positions[i],
            root_rotation=root_rotations[i],
            bone_rotations=bone_rotations,
        )
        frames.append(frame)

    return CanonicalMotion(
        name=metadata["name"],
        source_file=metadata["source_file"],
        fps=metadata["fps"],
        num_frames=metadata["num_frames"],
        bone_names=bone_names,
        bone_hierarchy=metadata["bone_hierarchy"],
        frames=frames,
        duration=metadata.get("duration"),
        source_skeleton_type=metadata.get("source_skeleton_type", "mixamo"),
    )
