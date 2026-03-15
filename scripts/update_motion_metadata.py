#!/usr/bin/env python3
"""Update motion metadata after training completes.

This script updates the motion metadata with W&B run paths and training status.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fbx2robot.config import MOTIONS_DIR


def update_metadata(
    motion_name: str,
    wandb_run_path: str,
    training_status: str = "trained",
    quality_notes: str = None,
):
    """Update metadata for a motion.

    Args:
        motion_name: Name of the motion
        wandb_run_path: W&B run path (e.g., "entity/project/runs/run_id")
        training_status: New training status
        quality_notes: Optional notes about quality
    """
    motion_dir = MOTIONS_DIR / motion_name
    metadata_path = motion_dir / "metadata.json"

    if not metadata_path.exists():
        print(f"[WARN] Metadata not found at {metadata_path}")
        print(f"Creating new metadata file...")
        metadata = {
            "motion_name": motion_name,
            "pipeline_version": "0.1.0",
        }
    else:
        with open(metadata_path) as f:
            metadata = json.load(f)

    # Update fields
    metadata["wandb_training_run"] = wandb_run_path
    metadata["training_status"] = training_status
    if quality_notes:
        metadata["quality_notes"] = quality_notes

    # Save
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"[OK] Updated metadata for {motion_name}")
    print(f"     W&B Run: {wandb_run_path}")
    print(f"     Status: {training_status}")


def main():
    parser = argparse.ArgumentParser(description="Update motion metadata")
    parser.add_argument("motion_name", help="Name of the motion to update")
    parser.add_argument("--wandb-run", required=True, help="W&B run path")
    parser.add_argument(
        "--status", default="trained", help="Training status (default: trained)"
    )
    parser.add_argument("--notes", help="Quality notes")

    args = parser.parse_args()

    update_metadata(
        motion_name=args.motion_name,
        wandb_run_path=args.wandb_run,
        training_status=args.status,
        quality_notes=args.notes,
    )


if __name__ == "__main__":
    main()
