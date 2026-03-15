"""Retarget Mixamo humanoid motion to G1 29-DOF joint space.

This module converts motion from Mixamo skeleton to Unitree G1 robot joints.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
from scipy.spatial.transform import Rotation

from fbx2robot.config import (
    G1_JOINT_NAMES,
    G1_JOINT_LIMITS,
    MIXAMO_TO_G1_MAPPING,
)
from fbx2robot.canonical.schema import CanonicalMotion


@dataclass
class RetargetedMotion:
    """Retargeted motion data for G1 robot."""

    name: str
    fps: float
    num_frames: int

    # Root trajectory
    root_positions: np.ndarray  # (N, 3)
    root_rotations: np.ndarray  # (N, 4) quaternion (x, y, z, w) for LAFAN format

    # Joint angles
    joint_positions: np.ndarray  # (N, 29)

    # Metadata
    source_file: str = ""
    processing_notes: List[str] = None

    def __post_init__(self):
        if self.processing_notes is None:
            self.processing_notes = []


class MixamoToG1Retargeter:
    """Retarget Mixamo motion to G1 joints."""

    # Mapping from Mixamo bones to G1 joints with axis extraction
    BONE_TO_JOINT_MAP = {
        # Left leg
        "mixamorig:LeftUpLeg": [
            ("left_hip_pitch", "x"),
            ("left_hip_roll", "z"),
            ("left_hip_yaw", "y"),
        ],
        "mixamorig:LeftLeg": [("left_knee", "x")],
        "mixamorig:LeftFoot": [
            ("left_ankle_pitch", "x"),
            ("left_ankle_roll", "z"),
        ],
        # Right leg
        "mixamorig:RightUpLeg": [
            ("right_hip_pitch", "x"),
            ("right_hip_roll", "z"),
            ("right_hip_yaw", "y"),
        ],
        "mixamorig:RightLeg": [("right_knee", "x")],
        "mixamorig:RightFoot": [
            ("right_ankle_pitch", "x"),
            ("right_ankle_roll", "z"),
        ],
        # Spine/waist - map from Spine1 (mid-spine)
        "mixamorig:Spine1": [
            ("waist_pitch", "x"),
            ("waist_roll", "z"),
            ("waist_yaw", "y"),
        ],
        # Left arm
        "mixamorig:LeftArm": [
            ("left_shoulder_pitch", "x"),
            ("left_shoulder_roll", "z"),
            ("left_shoulder_yaw", "y"),
        ],
        "mixamorig:LeftForeArm": [("left_elbow", "x")],
        "mixamorig:LeftHand": [
            ("left_wrist_pitch", "x"),
            ("left_wrist_roll", "z"),
            ("left_wrist_yaw", "y"),
        ],
        # Right arm
        "mixamorig:RightArm": [
            ("right_shoulder_pitch", "x"),
            ("right_shoulder_roll", "z"),
            ("right_shoulder_yaw", "y"),
        ],
        "mixamorig:RightForeArm": [("right_elbow", "x")],
        "mixamorig:RightHand": [
            ("right_wrist_pitch", "x"),
            ("right_wrist_roll", "z"),
            ("right_wrist_yaw", "y"),
        ],
    }

    def __init__(
        self,
        scale_factor: float = 1.0,
        apply_joint_limits: bool = True,
        smooth_window: int = 3,
    ):
        """Initialize retargeter.

        Args:
            scale_factor: Scale factor for root positions
            apply_joint_limits: Whether to clamp joints to limits
            smooth_window: Window size for temporal smoothing (0 to disable)
        """
        self.scale_factor = scale_factor
        self.apply_joint_limits = apply_joint_limits
        self.smooth_window = smooth_window

    def quat_to_euler(
        self, quat: np.ndarray, seq: str = "xyz"
    ) -> np.ndarray:
        """Convert quaternion (w,x,y,z) to euler angles.

        Args:
            quat: Quaternion array [w, x, y, z]
            seq: Euler angle sequence

        Returns:
            Euler angles in radians
        """
        # scipy uses [x, y, z, w] format
        quat_scipy = np.array([quat[1], quat[2], quat[3], quat[0]])
        rot = Rotation.from_quat(quat_scipy)
        return rot.as_euler(seq, degrees=False)

    def extract_joint_angle(
        self, quat: np.ndarray, axis: str
    ) -> float:
        """Extract single joint angle from quaternion.

        Args:
            quat: Quaternion [w, x, y, z]
            axis: 'x', 'y', or 'z'

        Returns:
            Joint angle in radians
        """
        euler = self.quat_to_euler(quat, seq="xyz")
        axis_map = {"x": 0, "y": 1, "z": 2}
        return euler[axis_map[axis]]

    def clamp_joint(self, value: float, joint_name: str) -> float:
        """Clamp joint angle to limits."""
        if not self.apply_joint_limits:
            return value
        if joint_name in G1_JOINT_LIMITS:
            low, high = G1_JOINT_LIMITS[joint_name]
            return np.clip(value, low, high)
        return value

    def smooth_trajectory(self, values: np.ndarray) -> np.ndarray:
        """Apply temporal smoothing to trajectory."""
        if self.smooth_window <= 1:
            return values

        kernel = np.ones(self.smooth_window) / self.smooth_window
        # Pad to handle edges
        padded = np.pad(values, self.smooth_window // 2, mode="edge")
        smoothed = np.convolve(padded, kernel, mode="valid")
        return smoothed[: len(values)]

    def retarget_frame(
        self, bone_rotations: Dict[str, np.ndarray]
    ) -> np.ndarray:
        """Retarget a single frame's bone rotations to G1 joints.

        Args:
            bone_rotations: Dict mapping bone name to quaternion [w,x,y,z]

        Returns:
            Array of 29 joint angles
        """
        joint_angles = np.zeros(29)

        for bone_name, joint_mappings in self.BONE_TO_JOINT_MAP.items():
            if bone_name not in bone_rotations:
                continue

            quat = bone_rotations[bone_name]

            for joint_name, axis in joint_mappings:
                angle = self.extract_joint_angle(quat, axis)
                angle = self.clamp_joint(angle, joint_name)

                joint_idx = G1_JOINT_NAMES.index(joint_name)
                joint_angles[joint_idx] = angle

        return joint_angles

    def convert_root_quat_to_lafan(self, quat_wxyz: np.ndarray) -> np.ndarray:
        """Convert quaternion from (w,x,y,z) to LAFAN format (x,y,z,w)."""
        return np.array([quat_wxyz[1], quat_wxyz[2], quat_wxyz[3], quat_wxyz[0]])

    def retarget(self, motion: CanonicalMotion) -> RetargetedMotion:
        """Retarget canonical motion to G1.

        Args:
            motion: CanonicalMotion from FBX extraction

        Returns:
            RetargetedMotion for G1 robot
        """
        num_frames = motion.num_frames
        notes = []

        # Extract root trajectory
        root_positions = np.zeros((num_frames, 3))
        root_rotations = np.zeros((num_frames, 4))

        for i, frame in enumerate(motion.frames):
            # Scale and transform root position
            pos = frame.root_position * self.scale_factor
            root_positions[i] = pos

            # Convert root rotation to LAFAN format (x,y,z,w)
            root_rotations[i] = self.convert_root_quat_to_lafan(frame.root_rotation)

        # Extract joint angles for each frame
        joint_positions = np.zeros((num_frames, 29))

        # Track which bones were found
        found_bones = set()
        missing_bones = set()

        for i, frame in enumerate(motion.frames):
            joint_positions[i] = self.retarget_frame(frame.bone_rotations)

            # Track bone coverage
            for bone_name in self.BONE_TO_JOINT_MAP.keys():
                if bone_name in frame.bone_rotations:
                    found_bones.add(bone_name)
                else:
                    missing_bones.add(bone_name)

        # Report coverage
        if found_bones:
            notes.append(f"Found {len(found_bones)} Mixamo bones")
        if missing_bones:
            notes.append(f"Missing bones: {missing_bones}")

        # Apply temporal smoothing
        if self.smooth_window > 1:
            for j in range(29):
                joint_positions[:, j] = self.smooth_trajectory(joint_positions[:, j])
            notes.append(f"Applied smoothing (window={self.smooth_window})")

        # Normalize root to start near origin
        root_positions[:, :2] -= root_positions[0, :2]

        return RetargetedMotion(
            name=motion.name,
            fps=motion.fps,
            num_frames=num_frames,
            root_positions=root_positions,
            root_rotations=root_rotations,
            joint_positions=joint_positions,
            source_file=motion.source_file,
            processing_notes=notes,
        )


def retarget_to_g1(
    motion: CanonicalMotion,
    scale_factor: float = 1.0,
    apply_limits: bool = True,
    smooth: int = 3,
) -> RetargetedMotion:
    """Convenience function to retarget motion to G1.

    Args:
        motion: CanonicalMotion from FBX
        scale_factor: Position scale factor
        apply_limits: Clamp to joint limits
        smooth: Smoothing window size

    Returns:
        RetargetedMotion for G1
    """
    retargeter = MixamoToG1Retargeter(
        scale_factor=scale_factor,
        apply_joint_limits=apply_limits,
        smooth_window=smooth,
    )
    return retargeter.retarget(motion)
