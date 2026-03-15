"""Canonical motion representation schema.

This defines the intermediate representation between FBX extraction and G1 retargeting.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np


@dataclass
class MotionFrame:
    """A single frame of motion data."""

    frame_index: int
    timestamp: float

    # Root transform (world space)
    root_position: np.ndarray  # shape (3,) - x, y, z
    root_rotation: np.ndarray  # shape (4,) - quaternion (w, x, y, z)

    # Bone rotations (local space, relative to parent)
    # Dict mapping bone name to rotation quaternion (w, x, y, z)
    bone_rotations: Dict[str, np.ndarray] = field(default_factory=dict)

    # Optional: bone positions for debugging/visualization
    bone_positions: Optional[Dict[str, np.ndarray]] = None


@dataclass
class CanonicalMotion:
    """Canonical motion representation.

    This is the intermediate format between FBX extraction and G1 retargeting.
    """

    # Metadata
    name: str
    source_file: str
    fps: float
    num_frames: int

    # Skeleton info
    bone_names: List[str]
    bone_hierarchy: Dict[str, Optional[str]]  # child -> parent mapping

    # Motion data
    frames: List[MotionFrame]

    # Optional metadata
    duration: Optional[float] = None
    source_skeleton_type: str = "mixamo"

    def __post_init__(self):
        if self.duration is None:
            self.duration = self.num_frames / self.fps if self.fps > 0 else 0.0

    def get_root_trajectory(self) -> np.ndarray:
        """Get root position trajectory as (N, 3) array."""
        return np.array([f.root_position for f in self.frames])

    def get_root_rotations(self) -> np.ndarray:
        """Get root rotation trajectory as (N, 4) array."""
        return np.array([f.root_rotation for f in self.frames])

    def get_bone_trajectory(self, bone_name: str) -> np.ndarray:
        """Get bone rotation trajectory as (N, 4) array."""
        rotations = []
        for frame in self.frames:
            if bone_name in frame.bone_rotations:
                rotations.append(frame.bone_rotations[bone_name])
            else:
                rotations.append(np.array([1.0, 0.0, 0.0, 0.0]))  # identity
        return np.array(rotations)

    def validate(self) -> List[str]:
        """Validate motion data and return list of issues."""
        issues = []

        if self.num_frames != len(self.frames):
            issues.append(
                f"Frame count mismatch: {self.num_frames} vs {len(self.frames)}"
            )

        if self.fps <= 0:
            issues.append(f"Invalid FPS: {self.fps}")

        for i, frame in enumerate(self.frames):
            # Check root position
            if np.any(np.isnan(frame.root_position)):
                issues.append(f"Frame {i}: NaN in root position")
            if np.any(np.isinf(frame.root_position)):
                issues.append(f"Frame {i}: Inf in root position")

            # Check root rotation
            if np.any(np.isnan(frame.root_rotation)):
                issues.append(f"Frame {i}: NaN in root rotation")
            quat_norm = np.linalg.norm(frame.root_rotation)
            if not (0.99 < quat_norm < 1.01):
                issues.append(
                    f"Frame {i}: Root quaternion not normalized (norm={quat_norm:.4f})"
                )

            # Check bone rotations
            for bone_name, rot in frame.bone_rotations.items():
                if np.any(np.isnan(rot)):
                    issues.append(f"Frame {i}: NaN in {bone_name} rotation")
                bone_quat_norm = np.linalg.norm(rot)
                if not (0.99 < bone_quat_norm < 1.01):
                    issues.append(
                        f"Frame {i}: {bone_name} quaternion not normalized "
                        f"(norm={bone_quat_norm:.4f})"
                    )

        return issues
