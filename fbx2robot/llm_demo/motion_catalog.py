"""Motion catalog for the LLM demo layer.

This module manages the catalog of available trained motions
and their metadata for the judge-facing demo.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from fbx2robot.config import MOTIONS_DIR


@dataclass
class MotionEntry:
    """A single motion in the catalog."""

    name: str
    display_name: str
    description: str
    keywords: List[str]
    csv_path: Optional[Path] = None
    wandb_artifact: Optional[str] = None
    wandb_run_path: Optional[str] = None
    duration_seconds: float = 0.0
    num_frames: int = 0
    training_status: str = "pending"  # pending, training, trained, failed
    quality_notes: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "keywords": self.keywords,
            "csv_path": str(self.csv_path) if self.csv_path else None,
            "wandb_artifact": self.wandb_artifact,
            "wandb_run_path": self.wandb_run_path,
            "duration_seconds": self.duration_seconds,
            "num_frames": self.num_frames,
            "training_status": self.training_status,
            "quality_notes": self.quality_notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MotionEntry":
        return cls(
            name=data["name"],
            display_name=data["display_name"],
            description=data["description"],
            keywords=data["keywords"],
            csv_path=Path(data["csv_path"]) if data.get("csv_path") else None,
            wandb_artifact=data.get("wandb_artifact"),
            wandb_run_path=data.get("wandb_run_path"),
            duration_seconds=data.get("duration_seconds", 0.0),
            num_frames=data.get("num_frames", 0),
            training_status=data.get("training_status", "pending"),
            quality_notes=data.get("quality_notes"),
        )


class MotionCatalog:
    """Catalog of available motions for the demo."""

    def __init__(self):
        self.motions: Dict[str, MotionEntry] = {}
        self._load_default_motions()

    def _load_default_motions(self):
        """Load default motion definitions."""
        default_motions = [
            MotionEntry(
                name="bow_greeting",
                display_name="Bow Greeting",
                description="A respectful bow greeting motion. The robot bends forward "
                "at the waist in a traditional greeting gesture.",
                keywords=[
                    "bow",
                    "greeting",
                    "hello",
                    "respect",
                    "formal",
                    "welcome",
                    "polite",
                    "japanese",
                    "asian",
                ],
            ),
            MotionEntry(
                name="standing_greeting",
                display_name="Standing Greeting",
                description="A standing wave greeting motion. The robot raises its arm "
                "and waves in a friendly greeting gesture.",
                keywords=[
                    "wave",
                    "hello",
                    "greeting",
                    "friendly",
                    "casual",
                    "welcome",
                    "hi",
                    "standing",
                ],
            ),
            MotionEntry(
                name="celebratory_gesture",
                display_name="Celebratory Gesture",
                description="An excited celebratory motion. The robot raises its arms "
                "in a victory or celebration pose.",
                keywords=[
                    "celebrate",
                    "victory",
                    "win",
                    "excited",
                    "happy",
                    "cheer",
                    "triumph",
                    "joy",
                ],
            ),
            MotionEntry(
                name="short_dance_loop",
                display_name="Dance",
                description="A short dance loop motion. The robot performs rhythmic "
                "movements in a dancing pattern.",
                keywords=[
                    "dance",
                    "dancing",
                    "rhythm",
                    "music",
                    "groove",
                    "move",
                    "party",
                    "fun",
                ],
            ),
            MotionEntry(
                name="sidestep_arm_sweep",
                display_name="Sidestep with Arm Sweep",
                description="A lateral stepping motion with arm movements. The robot "
                "steps to the side while sweeping its arms.",
                keywords=[
                    "sidestep",
                    "lateral",
                    "arm",
                    "sweep",
                    "step",
                    "movement",
                    "dynamic",
                ],
            ),
        ]

        for motion in default_motions:
            self.motions[motion.name] = motion

        # Try to load metadata from processed motions
        self._load_from_metadata()

    def _load_from_metadata(self):
        """Load motion info from processed metadata files."""
        if not MOTIONS_DIR.exists():
            return

        for motion_dir in MOTIONS_DIR.iterdir():
            if not motion_dir.is_dir():
                continue

            metadata_path = motion_dir / "metadata.json"
            if not metadata_path.exists():
                continue

            try:
                with open(metadata_path) as f:
                    metadata = json.load(f)

                motion_name = metadata.get("motion_name", motion_dir.name)
                if motion_name in self.motions:
                    entry = self.motions[motion_name]
                    entry.csv_path = Path(metadata.get("csv_path", ""))
                    entry.duration_seconds = metadata.get("duration_seconds", 0.0)
                    entry.num_frames = metadata.get("num_frames", 0)
                    entry.wandb_artifact = metadata.get("wandb_motion_artifact")
                    entry.wandb_run_path = metadata.get("wandb_training_run")
                    if entry.wandb_run_path:
                        entry.training_status = "trained"
                    elif entry.csv_path and Path(entry.csv_path).exists():
                        entry.training_status = "ready"
            except Exception as e:
                print(f"Warning: Failed to load metadata from {metadata_path}: {e}")

    def get_motion(self, name: str) -> Optional[MotionEntry]:
        """Get a motion by name."""
        return self.motions.get(name)

    def list_motions(self) -> List[MotionEntry]:
        """List all motions."""
        return list(self.motions.values())

    def list_trained_motions(self) -> List[MotionEntry]:
        """List only trained motions."""
        return [m for m in self.motions.values() if m.training_status == "trained"]

    def list_available_motions(self) -> List[MotionEntry]:
        """List motions that have CSV files ready."""
        return [
            m
            for m in self.motions.values()
            if m.csv_path and Path(m.csv_path).exists()
        ]

    def search_by_keyword(self, query: str) -> List[MotionEntry]:
        """Search motions by keyword matching."""
        query_lower = query.lower()
        results = []

        for motion in self.motions.values():
            # Check name and display name
            if query_lower in motion.name.lower():
                results.append(motion)
                continue
            if query_lower in motion.display_name.lower():
                results.append(motion)
                continue

            # Check keywords
            for keyword in motion.keywords:
                if query_lower in keyword.lower():
                    results.append(motion)
                    break

            # Check description
            if query_lower in motion.description.lower():
                results.append(motion)

        return results

    def update_motion(
        self,
        name: str,
        wandb_artifact: Optional[str] = None,
        wandb_run_path: Optional[str] = None,
        training_status: Optional[str] = None,
        quality_notes: Optional[str] = None,
    ):
        """Update motion metadata."""
        if name not in self.motions:
            return

        motion = self.motions[name]
        if wandb_artifact:
            motion.wandb_artifact = wandb_artifact
        if wandb_run_path:
            motion.wandb_run_path = wandb_run_path
        if training_status:
            motion.training_status = training_status
        if quality_notes:
            motion.quality_notes = quality_notes

    def save_catalog(self, path: Path):
        """Save catalog to JSON file."""
        data = {name: motion.to_dict() for name, motion in self.motions.items()}
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def get_summary(self) -> str:
        """Get a text summary of the catalog."""
        lines = ["Motion Catalog Summary:", "=" * 40]

        for motion in self.motions.values():
            status_icon = {
                "trained": "[TRAINED]",
                "training": "[TRAINING]",
                "ready": "[READY]",
                "pending": "[PENDING]",
                "failed": "[FAILED]",
            }.get(motion.training_status, "[?]")

            lines.append(f"\n{status_icon} {motion.display_name}")
            lines.append(f"   Name: {motion.name}")
            lines.append(f"   {motion.description[:60]}...")
            if motion.duration_seconds > 0:
                lines.append(f"   Duration: {motion.duration_seconds:.1f}s")
            if motion.wandb_run_path:
                lines.append(f"   Run: {motion.wandb_run_path}")

        return "\n".join(lines)


# Global catalog instance
_catalog: Optional[MotionCatalog] = None


def get_catalog() -> MotionCatalog:
    """Get the global motion catalog."""
    global _catalog
    if _catalog is None:
        _catalog = MotionCatalog()
    return _catalog
