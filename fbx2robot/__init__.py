"""FBX2Robot: FBX Motion Ingestion, Retargeting, and Policy Training Pipeline.

This package provides tools to:
1. Ingest humanoid animation FBX files
2. Extract skeleton and animation data
3. Retarget motion to Unitree G1 29-DOF joint space
4. Export mjlab-compatible motion CSV files
5. Integrate with W&B motion registry and training
"""

__version__ = "0.1.0"

from fbx2robot.config import Config, G1_JOINT_NAMES, G1_JOINT_ORDER
