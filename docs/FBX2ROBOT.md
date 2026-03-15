# FBX2Robot Pipeline Documentation

## Overview

FBX2Robot is a pipeline for converting Mixamo-style FBX humanoid animations into motion data compatible with the Unitree G1 robot in mjlab.

## Pipeline Flow

```
FBX file
  ↓ Blender headless extraction
Canonical Motion (JSON/NPZ)
  ↓ Retargeting
G1 Joint Angles (29 DOF)
  ↓ Export
LAFAN-style CSV (36 columns)
  ↓ csv_to_npz.py
W&B Motion Registry
  ↓ train
Mjlab Policy
```

## Quick Start

### 1. Process a Single FBX File

```bash
python scripts/process_fbx.py process Mixamo/Greeting1-Quick\ Informal\ Bow.fbx \
    --motion-name bow_greeting \
    --output-dir data/motions/bow_greeting
```

### 2. Process All FBX Files

```bash
python scripts/run_motion_suite.py
```

### 3. Validate Output

```bash
python scripts/process_fbx.py validate data/motions/bow_greeting/robot_motion.csv
```

### 4. Show Configuration

```bash
python scripts/process_fbx.py info
```

## Output Files

For each processed motion, the pipeline creates:

| File | Description |
|------|-------------|
| `robot_motion.csv` | 36-column LAFAN-format motion file |
| `metadata.json` | Processing metadata |
| `canonical_motion.npz` | Intermediate representation |
| `*_extracted.json` | Raw Blender extraction |

## CSV Format

The output CSV has 36 columns per row:

| Columns | Data |
|---------|------|
| 0-2 | Base position (x, y, z) |
| 3-6 | Base quaternion (x, y, z, w) |
| 7-35 | 29 joint angles (radians) |

## G1 Joint Order

```
0: left_hip_pitch       15: left_shoulder_pitch
1: left_hip_roll        16: left_shoulder_roll
2: left_hip_yaw         17: left_shoulder_yaw
3: left_knee            18: left_elbow
4: left_ankle_pitch     19: left_wrist_roll
5: left_ankle_roll      20: left_wrist_pitch
6: right_hip_pitch      21: left_wrist_yaw
7: right_hip_roll       22: right_shoulder_pitch
8: right_hip_yaw        23: right_shoulder_roll
9: right_knee           24: right_shoulder_yaw
10: right_ankle_pitch   25: right_elbow
11: right_ankle_roll    26: right_wrist_roll
12: waist_yaw           27: right_wrist_pitch
13: waist_roll          28: right_wrist_yaw
14: waist_pitch
```

## Training Integration

After processing, use the existing mjlab flow:

```bash
# Convert CSV to NPZ and upload to W&B
uv run python src/mjlab/scripts/csv_to_npz.py \
    --input_file data/motions/bow_greeting/robot_motion.csv \
    --input_fps 30 \
    --output_name bow_greeting

# Train
uv run train Mjlab-Tracking-Flat-Unitree-G1 \
    --registry-name YOUR_ORG/wandb-registry-Motions/bow_greeting \
    --env.scene.num-envs 4096 \
    --agent.wandb-project fbx2robot-hackathon

# Play
uv run play Mjlab-Tracking-Flat-Unitree-G1 \
    --wandb-run-path YOUR_ORG/fbx2robot-hackathon/RUN_ID
```

## Requirements

- Blender 5.0+ (for headless FBX extraction)
- Python 3.10+
- scipy (for rotation math)
- numpy

## Troubleshooting

### Blender not found

Run `python scripts/find_blender.py` to locate Blender installations.

### Missing bones in retargeting

The retargeter looks for standard Mixamo bone names (`mixamorig:*`). If your FBX uses different naming, you may need to update the bone mapping in `fbx2robot/config.py`.

### NaN in output

Check that the source FBX has valid animation data and the skeleton is properly configured.
