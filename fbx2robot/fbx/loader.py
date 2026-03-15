"""High-level FBX loading interface."""

from pathlib import Path
from typing import Optional, Union

from fbx2robot.canonical.schema import CanonicalMotion
from fbx2robot.fbx.blender_backend import extract_fbx_motion


def load_fbx(
    fbx_path: Union[str, Path],
    motion_name: Optional[str] = None,
    output_dir: Optional[Union[str, Path]] = None,
) -> CanonicalMotion:
    """Load an FBX file and extract motion data.

    Args:
        fbx_path: Path to FBX file
        motion_name: Optional name for the motion (defaults to filename)
        output_dir: Optional directory for intermediate files

    Returns:
        CanonicalMotion object
    """
    fbx_path = Path(fbx_path)

    if motion_name is None:
        motion_name = fbx_path.stem.replace(" ", "_").replace("-", "_").lower()

    return extract_fbx_motion(
        fbx_path=fbx_path,
        motion_name=motion_name,
        output_dir=output_dir,
    )
