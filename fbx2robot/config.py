"""Configuration for the FBX2Robot pipeline."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Blender executable path
BLENDER_PATH = Path(r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe")

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MOTIONS_DIR = DATA_DIR / "motions"
MIXAMO_DIR = PROJECT_ROOT / "Mixamo"

# G1 Robot Configuration
G1_JOINT_NAMES = [
    "left_hip_pitch",
    "left_hip_roll",
    "left_hip_yaw",
    "left_knee",
    "left_ankle_pitch",
    "left_ankle_roll",
    "right_hip_pitch",
    "right_hip_roll",
    "right_hip_yaw",
    "right_knee",
    "right_ankle_pitch",
    "right_ankle_roll",
    "waist_yaw",
    "waist_roll",
    "waist_pitch",
    "left_shoulder_pitch",
    "left_shoulder_roll",
    "left_shoulder_yaw",
    "left_elbow",
    "left_wrist_roll",
    "left_wrist_pitch",
    "left_wrist_yaw",
    "right_shoulder_pitch",
    "right_shoulder_roll",
    "right_shoulder_yaw",
    "right_elbow",
    "right_wrist_roll",
    "right_wrist_pitch",
    "right_wrist_yaw",
]

G1_JOINT_ORDER = {name: i for i, name in enumerate(G1_JOINT_NAMES)}

# Mixamo bone names mapping
MIXAMO_BONE_NAMES = {
    "Hips": "mixamorig:Hips",
    "Spine": "mixamorig:Spine",
    "Spine1": "mixamorig:Spine1",
    "Spine2": "mixamorig:Spine2",
    "Neck": "mixamorig:Neck",
    "Head": "mixamorig:Head",
    "LeftShoulder": "mixamorig:LeftShoulder",
    "LeftArm": "mixamorig:LeftArm",
    "LeftForeArm": "mixamorig:LeftForeArm",
    "LeftHand": "mixamorig:LeftHand",
    "RightShoulder": "mixamorig:RightShoulder",
    "RightArm": "mixamorig:RightArm",
    "RightForeArm": "mixamorig:RightForeArm",
    "RightHand": "mixamorig:RightHand",
    "LeftUpLeg": "mixamorig:LeftUpLeg",
    "LeftLeg": "mixamorig:LeftLeg",
    "LeftFoot": "mixamorig:LeftFoot",
    "LeftToeBase": "mixamorig:LeftToeBase",
    "RightUpLeg": "mixamorig:RightUpLeg",
    "RightLeg": "mixamorig:RightLeg",
    "RightFoot": "mixamorig:RightFoot",
    "RightToeBase": "mixamorig:RightToeBase",
}

# Mapping from Mixamo bones to G1 joints
# Format: mixamo_bone -> (g1_joint_name, rotation_axis_mapping)
MIXAMO_TO_G1_MAPPING = {
    # Left leg
    "mixamorig:LeftUpLeg": {
        "left_hip_pitch": "X",
        "left_hip_roll": "Z",
        "left_hip_yaw": "Y",
    },
    "mixamorig:LeftLeg": {
        "left_knee": "X",
    },
    "mixamorig:LeftFoot": {
        "left_ankle_pitch": "X",
        "left_ankle_roll": "Z",
    },
    # Right leg
    "mixamorig:RightUpLeg": {
        "right_hip_pitch": "X",
        "right_hip_roll": "Z",
        "right_hip_yaw": "Y",
    },
    "mixamorig:RightLeg": {
        "right_knee": "X",
    },
    "mixamorig:RightFoot": {
        "right_ankle_pitch": "X",
        "right_ankle_roll": "Z",
    },
    # Spine/waist
    "mixamorig:Spine": {
        "waist_yaw": "Y",
        "waist_roll": "Z",
        "waist_pitch": "X",
    },
    # Left arm
    "mixamorig:LeftArm": {
        "left_shoulder_pitch": "X",
        "left_shoulder_roll": "Z",
        "left_shoulder_yaw": "Y",
    },
    "mixamorig:LeftForeArm": {
        "left_elbow": "X",
    },
    "mixamorig:LeftHand": {
        "left_wrist_roll": "Z",
        "left_wrist_pitch": "X",
        "left_wrist_yaw": "Y",
    },
    # Right arm
    "mixamorig:RightArm": {
        "right_shoulder_pitch": "X",
        "right_shoulder_roll": "Z",
        "right_shoulder_yaw": "Y",
    },
    "mixamorig:RightForeArm": {
        "right_elbow": "X",
    },
    "mixamorig:RightHand": {
        "right_wrist_roll": "Z",
        "right_wrist_pitch": "X",
        "right_wrist_yaw": "Y",
    },
}

# G1 joint limits (radians) - approximate values
G1_JOINT_LIMITS = {
    "left_hip_pitch": (-1.57, 1.57),
    "left_hip_roll": (-0.52, 0.52),
    "left_hip_yaw": (-0.52, 0.52),
    "left_knee": (0.0, 2.09),
    "left_ankle_pitch": (-0.87, 0.87),
    "left_ankle_roll": (-0.26, 0.26),
    "right_hip_pitch": (-1.57, 1.57),
    "right_hip_roll": (-0.52, 0.52),
    "right_hip_yaw": (-0.52, 0.52),
    "right_knee": (0.0, 2.09),
    "right_ankle_pitch": (-0.87, 0.87),
    "right_ankle_roll": (-0.26, 0.26),
    "waist_yaw": (-0.78, 0.78),
    "waist_roll": (-0.52, 0.52),
    "waist_pitch": (-0.52, 0.52),
    "left_shoulder_pitch": (-2.87, 2.87),
    "left_shoulder_roll": (-1.57, 1.57),
    "left_shoulder_yaw": (-1.57, 1.57),
    "left_elbow": (-2.61, 0.0),
    "left_wrist_roll": (-1.57, 1.57),
    "left_wrist_pitch": (-0.52, 0.52),
    "left_wrist_yaw": (-0.52, 0.52),
    "right_shoulder_pitch": (-2.87, 2.87),
    "right_shoulder_roll": (-1.57, 1.57),
    "right_shoulder_yaw": (-1.57, 1.57),
    "right_elbow": (0.0, 2.61),
    "right_wrist_roll": (-1.57, 1.57),
    "right_wrist_pitch": (-0.52, 0.52),
    "right_wrist_yaw": (-0.52, 0.52),
}


@dataclass
class Config:
    """Pipeline configuration."""

    blender_path: Path = BLENDER_PATH
    project_root: Path = PROJECT_ROOT
    data_dir: Path = DATA_DIR
    motions_dir: Path = MOTIONS_DIR
    mixamo_dir: Path = MIXAMO_DIR

    # Processing settings
    target_fps: float = 30.0
    output_fps: float = 50.0

    # W&B settings
    wandb_project: str = "fbx2robot-hackathon"
    wandb_entity: Optional[str] = None

    # OpenAI settings
    openai_api_key: Optional[str] = field(
        default_factory=lambda: os.environ.get("OPENAI_API_KEY")
    )

    def validate(self) -> bool:
        """Validate configuration."""
        if not self.blender_path.exists():
            raise FileNotFoundError(f"Blender not found at {self.blender_path}")
        if not self.project_root.exists():
            raise FileNotFoundError(f"Project root not found at {self.project_root}")
        return True


def get_config() -> Config:
    """Get default configuration."""
    return Config()
