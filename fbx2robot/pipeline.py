"""Main FBX2Robot pipeline.

This module orchestrates the full pipeline:
FBX -> Extract -> Canonical -> Retarget -> CSV -> (optionally) NPZ/W&B
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from fbx2robot.config import Config, get_config, MOTIONS_DIR
from fbx2robot.fbx import load_fbx
from fbx2robot.canonical import save_canonical
from fbx2robot.retarget import retarget_to_g1
from fbx2robot.export import export_to_csv, create_metadata, save_metadata


@dataclass
class PipelineResult:
    """Result of pipeline processing."""

    motion_name: str
    success: bool
    csv_path: Optional[Path] = None
    metadata_path: Optional[Path] = None
    canonical_path: Optional[Path] = None
    error: Optional[str] = None
    notes: list = None

    def __post_init__(self):
        if self.notes is None:
            self.notes = []


def process_fbx(
    fbx_path: Union[str, Path],
    motion_name: Optional[str] = None,
    output_dir: Optional[Union[str, Path]] = None,
    config: Optional[Config] = None,
    save_intermediate: bool = True,
    scale_factor: float = 1.0,
    apply_limits: bool = True,
    smooth_window: int = 3,
) -> PipelineResult:
    """Process an FBX file through the full pipeline.

    Args:
        fbx_path: Path to input FBX file
        motion_name: Optional motion name (defaults to filename)
        output_dir: Optional output directory
        config: Optional Config object
        save_intermediate: Whether to save canonical representation
        scale_factor: Position scale factor
        apply_limits: Clamp to joint limits
        smooth_window: Smoothing window size

    Returns:
        PipelineResult with paths and status
    """
    fbx_path = Path(fbx_path)
    config = config or get_config()

    # Derive motion name from filename if not provided
    if motion_name is None:
        motion_name = fbx_path.stem.replace(" ", "_").replace("-", "_").lower()

    # Set up output directory
    if output_dir is None:
        output_dir = MOTIONS_DIR / motion_name
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    result = PipelineResult(motion_name=motion_name, success=False)

    try:
        # Step 1: Extract motion from FBX
        print(f"\n[1/4] Extracting motion from {fbx_path.name}...")
        canonical = load_fbx(
            fbx_path=fbx_path,
            motion_name=motion_name,
            output_dir=output_dir,
        )
        result.notes.append(f"Extracted {canonical.num_frames} frames at {canonical.fps} FPS")
        result.notes.append(f"Found {len(canonical.bone_names)} bones")

        # Optionally save canonical representation
        if save_intermediate:
            canonical_path = output_dir / "canonical_motion.npz"
            save_canonical(canonical, canonical_path)
            result.canonical_path = canonical_path
            result.notes.append(f"Saved canonical to {canonical_path}")

        # Step 2: Retarget to G1
        print(f"[2/4] Retargeting to G1 29-DOF...")
        retargeted = retarget_to_g1(
            canonical,
            scale_factor=scale_factor,
            apply_limits=apply_limits,
            smooth=smooth_window,
        )
        result.notes.extend(retargeted.processing_notes)

        # Step 3: Export to CSV
        print(f"[3/4] Exporting to CSV...")
        csv_path = output_dir / "robot_motion.csv"
        export_to_csv(retargeted, csv_path)
        result.csv_path = csv_path

        # Step 4: Create metadata
        print(f"[4/4] Creating metadata...")
        metadata = create_metadata(
            motion=retargeted,
            source_fbx=fbx_path,
            csv_path=csv_path,
        )
        metadata_path = output_dir / "metadata.json"
        save_metadata(metadata, metadata_path)
        result.metadata_path = metadata_path

        result.success = True
        print(f"\n[OK] Successfully processed {motion_name}")
        print(f"  Output: {output_dir}")

    except Exception as e:
        result.error = str(e)
        result.notes.append(f"Error: {e}")
        print(f"\n[FAIL] Failed to process {motion_name}: {e}")
        import traceback
        traceback.print_exc()

    return result


def process_all_motions(
    config: Optional[Config] = None,
) -> dict:
    """Process all FBX files in the Mixamo directory.

    Returns:
        Dictionary mapping motion names to PipelineResults
    """
    config = config or get_config()
    results = {}

    if not config.mixamo_dir.exists():
        print(f"Mixamo directory not found: {config.mixamo_dir}")
        return results

    fbx_files = list(config.mixamo_dir.glob("*.fbx"))
    print(f"Found {len(fbx_files)} FBX files in {config.mixamo_dir}")

    for fbx_path in fbx_files:
        result = process_fbx(fbx_path, config=config)
        results[result.motion_name] = result

    # Summary
    print(f"\n{'='*50}")
    print("Processing Summary:")
    successes = sum(1 for r in results.values() if r.success)
    print(f"  Successful: {successes}/{len(results)}")
    for name, result in results.items():
        status = "✓" if result.success else "✗"
        print(f"  {status} {name}")
        if not result.success and result.error:
            print(f"      Error: {result.error}")

    return results
