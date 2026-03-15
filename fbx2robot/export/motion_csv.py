"""Export retargeted motion to mjlab-compatible CSV format.

The CSV format is the LAFAN-style format used by mjlab:
- Columns 0-2: Base position (x, y, z)
- Columns 3-6: Base orientation quaternion (x, y, z, w)
- Columns 7-35: 29 joint angles in radians
"""

from pathlib import Path
from typing import List, Tuple, Union
import numpy as np

from fbx2robot.retarget.mixamo_to_g1 import RetargetedMotion


def validate_motion(motion: RetargetedMotion) -> Tuple[bool, List[str]]:
    """Validate motion data before export.

    Args:
        motion: RetargetedMotion to validate

    Returns:
        Tuple of (is_valid, list of issues)
    """
    issues = []

    # Check shapes
    if motion.root_positions.shape != (motion.num_frames, 3):
        issues.append(
            f"Root positions shape mismatch: {motion.root_positions.shape} "
            f"vs expected ({motion.num_frames}, 3)"
        )

    if motion.root_rotations.shape != (motion.num_frames, 4):
        issues.append(
            f"Root rotations shape mismatch: {motion.root_rotations.shape} "
            f"vs expected ({motion.num_frames}, 4)"
        )

    if motion.joint_positions.shape != (motion.num_frames, 29):
        issues.append(
            f"Joint positions shape mismatch: {motion.joint_positions.shape} "
            f"vs expected ({motion.num_frames}, 29)"
        )

    # Check for NaNs
    if np.any(np.isnan(motion.root_positions)):
        issues.append("NaN values in root positions")

    if np.any(np.isnan(motion.root_rotations)):
        issues.append("NaN values in root rotations")

    if np.any(np.isnan(motion.joint_positions)):
        nan_frames = np.where(np.any(np.isnan(motion.joint_positions), axis=1))[0]
        issues.append(f"NaN values in joint positions at frames: {nan_frames[:5]}...")

    # Check quaternion normalization
    quat_norms = np.linalg.norm(motion.root_rotations, axis=1)
    bad_quats = np.where(np.abs(quat_norms - 1.0) > 0.01)[0]
    if len(bad_quats) > 0:
        issues.append(
            f"Unnormalized quaternions at frames: {bad_quats[:5]}... "
            f"(norms: {quat_norms[bad_quats[:5]]})"
        )

    # Check frame count
    if motion.num_frames < 1:
        issues.append(f"No frames in motion")

    # Check FPS
    if motion.fps <= 0:
        issues.append(f"Invalid FPS: {motion.fps}")

    return len(issues) == 0, issues


def export_to_csv(
    motion: RetargetedMotion,
    output_path: Union[str, Path],
    normalize_quaternions: bool = True,
) -> Path:
    """Export retargeted motion to mjlab CSV format.

    Args:
        motion: RetargetedMotion to export
        output_path: Path for output CSV file
        normalize_quaternions: Whether to normalize quaternions

    Returns:
        Path to exported CSV file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Validate
    is_valid, issues = validate_motion(motion)
    if not is_valid:
        print("Warning: Motion validation issues:")
        for issue in issues:
            print(f"  - {issue}")

    # Prepare data array (N, 36)
    data = np.zeros((motion.num_frames, 36))

    # Columns 0-2: Base position
    data[:, 0:3] = motion.root_positions

    # Columns 3-6: Base quaternion (x, y, z, w)
    quats = motion.root_rotations.copy()
    if normalize_quaternions:
        norms = np.linalg.norm(quats, axis=1, keepdims=True)
        quats = quats / np.where(norms > 0, norms, 1.0)
    data[:, 3:7] = quats

    # Columns 7-35: Joint angles
    data[:, 7:36] = motion.joint_positions

    # Save CSV without header
    np.savetxt(
        output_path,
        data,
        delimiter=",",
        fmt="%.6f",
    )

    print(f"Exported {motion.num_frames} frames to {output_path}")
    return output_path


def validate_csv(csv_path: Union[str, Path]) -> Tuple[bool, List[str]]:
    """Validate an exported CSV file.

    Args:
        csv_path: Path to CSV file

    Returns:
        Tuple of (is_valid, list of issues)
    """
    csv_path = Path(csv_path)
    issues = []

    if not csv_path.exists():
        return False, [f"File not found: {csv_path}"]

    try:
        data = np.loadtxt(csv_path, delimiter=",")
    except Exception as e:
        return False, [f"Failed to load CSV: {e}"]

    # Check shape
    if data.ndim == 1:
        data = data.reshape(1, -1)

    if data.shape[1] != 36:
        issues.append(f"Expected 36 columns, got {data.shape[1]}")
        return False, issues

    num_frames = data.shape[0]
    if num_frames < 1:
        issues.append("No frames in CSV")
        return False, issues

    # Check for NaNs
    if np.any(np.isnan(data)):
        nan_locs = np.where(np.isnan(data))
        issues.append(f"NaN values at {len(nan_locs[0])} locations")

    # Check quaternions (columns 3-6)
    quats = data[:, 3:7]
    quat_norms = np.linalg.norm(quats, axis=1)
    bad_quats = np.where(np.abs(quat_norms - 1.0) > 0.01)[0]
    if len(bad_quats) > 0:
        issues.append(
            f"{len(bad_quats)} frames have unnormalized quaternions "
            f"(frames {bad_quats[:3]}...)"
        )

    # Check joint angles are reasonable
    joints = data[:, 7:36]
    if np.any(np.abs(joints) > 10):  # radians
        extreme_joints = np.where(np.abs(joints) > 10)
        issues.append(
            f"Extreme joint angles (>10 rad) at {len(extreme_joints[0])} locations"
        )

    print(f"CSV validation: {num_frames} frames, {len(issues)} issues")
    return len(issues) == 0, issues
