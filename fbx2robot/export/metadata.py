"""Metadata generation for processed motions."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from fbx2robot.config import BLENDER_PATH
from fbx2robot.retarget.mixamo_to_g1 import RetargetedMotion


def create_metadata(
    motion: RetargetedMotion,
    source_fbx: Union[str, Path],
    csv_path: Union[str, Path],
    wandb_artifact: Optional[str] = None,
    wandb_run: Optional[str] = None,
    extra_notes: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create metadata dictionary for a processed motion.

    Args:
        motion: RetargetedMotion object
        source_fbx: Path to source FBX file
        csv_path: Path to exported CSV
        wandb_artifact: Optional W&B artifact name
        wandb_run: Optional W&B run path
        extra_notes: Optional additional metadata

    Returns:
        Metadata dictionary
    """
    metadata = {
        "motion_name": motion.name,
        "source_file": str(source_fbx),
        "source_fps": motion.fps,
        "num_frames": motion.num_frames,
        "duration_seconds": motion.num_frames / motion.fps if motion.fps > 0 else 0,
        "blender_path_used": str(BLENDER_PATH),
        "processing_timestamp": datetime.now().isoformat(),
        "retarget_version": "0.1.0",
        "csv_path": str(csv_path),
        "wandb_motion_artifact": wandb_artifact,
        "wandb_training_run": wandb_run,
        "processing_notes": motion.processing_notes,
        "joint_count": 29,
        "csv_columns": 36,
    }

    if extra_notes:
        metadata["extra_notes"] = extra_notes

    return metadata


def save_metadata(
    metadata: Dict[str, Any],
    output_path: Union[str, Path],
) -> Path:
    """Save metadata to JSON file.

    Args:
        metadata: Metadata dictionary
        output_path: Path for output JSON file

    Returns:
        Path to saved file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(metadata, f, indent=2, default=str)

    print(f"Saved metadata to {output_path}")
    return output_path


def load_metadata(json_path: Union[str, Path]) -> Dict[str, Any]:
    """Load metadata from JSON file.

    Args:
        json_path: Path to JSON file

    Returns:
        Metadata dictionary
    """
    with open(json_path) as f:
        return json.load(f)
