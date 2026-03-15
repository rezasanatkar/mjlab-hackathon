# mjlab-hackathon Repository Capabilities

> This document describes the capabilities, features, and input requirements of the mjlab-hackathon repository for use by planning agents.

---

## 1. Repository Purpose

**mjlab** is a GPU-accelerated reinforcement learning framework for robotics that combines:
- **Isaac Lab's manager-based API** - Modular MDP component design
- **MuJoCo Warp** - GPU-accelerated physics simulation from Google DeepMind

**This hackathon fork** extends mjlab with a complete **motion imitation pipeline** for the Unitree G1 humanoid robot.

---

## 2. Core Capabilities

### 2.1 Training Capabilities

| Capability | Description |
|------------|-------------|
| **GPU-Accelerated Training** | Parallel simulation of thousands of environments on NVIDIA GPUs |
| **Multi-GPU Training** | Scale training across multiple GPUs with `--gpu-ids` flag |
| **PPO Algorithm** | Uses rsl-rl-lib for Proximal Policy Optimization |
| **Curriculum Learning** | Progressive difficulty increase during training |
| **Domain Randomization** | Randomize physics parameters (friction, mass, encoder bias, etc.) |
| **Experiment Tracking** | Weights & Biases integration for logging and checkpoints |
| **ONNX Export** | Export trained policies for real robot deployment |

### 2.2 Simulation Capabilities

| Capability | Description |
|------------|-------------|
| **Physics Simulation** | MuJoCo Warp GPU-accelerated physics |
| **Terrain Generation** | Procedural terrains (flat, rough, stairs, slopes, obstacles) |
| **Sensor Simulation** | IMU, contact sensors, raycast sensors, cameras |
| **Collision Detection** | Self-collision and environment collision |
| **Visualization** | Native MuJoCo viewer, Viser web viewer, offscreen rendering |

### 2.3 Motion Processing Capabilities

| Capability | Description |
|------------|-------------|
| **CSV Motion Loading** | Load motion data from LAFAN-format CSV files |
| **Motion Interpolation** | Resample motions to different frame rates |
| **Velocity Computation** | Automatically compute joint/body velocities from positions |
| **NPZ Conversion** | Convert CSV to NPZ format for training |
| **Motion Registry** | Upload/download motions via Weights & Biases registry |
| **Rerun Visualization** | 3D visualization of motion data |

---

## 3. Available Task Types

### 3.1 Motion Tracking / Imitation (`Mjlab-Tracking-*`)

**Purpose**: Train a robot to mimic reference motion data.

**Task IDs**:
- `Mjlab-Tracking-Flat-Unitree-G1` - G1 humanoid on flat terrain

**Features**:
- Tracks body positions, orientations, and velocities
- Supports any motion from CSV/NPZ format
- Domain randomization (friction, COM offset, encoder bias)
- External push disturbances

**Required Inputs**:
- Motion file (CSV or NPZ via W&B registry)

### 3.2 Velocity Tracking (`Mjlab-Velocity-*`)

**Purpose**: Train a robot to follow velocity commands (walk/run in any direction).

**Task IDs**:
- `Mjlab-Velocity-Flat-Unitree-G1` - G1 humanoid on flat terrain
- `Mjlab-Velocity-Rough-Unitree-G1` - G1 humanoid on rough terrain
- `Mjlab-Velocity-Flat-Unitree-Go1` - Go1 quadruped on flat terrain
- `Mjlab-Velocity-Rough-Unitree-Go1` - Go1 quadruped on rough terrain

**Features**:
- Random velocity commands (linear x/y, angular z)
- Heading control
- Terrain curriculum
- Height scan observations

### 3.3 Manipulation (`Mjlab-LiftCube-*`)

**Purpose**: Train a robot arm to lift objects.

**Task IDs**:
- `Mjlab-LiftCube-i2rt-YAM` - YAM robot arm lifting cubes

**Features**:
- End-effector to object distance observations
- Staged rewards (reaching → grasping → lifting)
- Collision termination

---

## 4. Available Robots

| Robot | Type | DOF | Task Support |
|-------|------|-----|--------------|
| **Unitree G1** | Humanoid | 29 | Velocity tracking, Motion imitation |
| **Unitree Go1** | Quadruped | 12 | Velocity tracking |
| **i2rt YAM** | Robot Arm | 6 | Manipulation |

### 4.1 Unitree G1 Joint Order (29 joints)

```
Index | Joint Name              | Index | Joint Name
------|-------------------------|-------|------------------------
0     | left_hip_pitch          | 15    | left_shoulder_pitch
1     | left_hip_roll           | 16    | left_shoulder_roll
2     | left_hip_yaw            | 17    | left_shoulder_yaw
3     | left_knee               | 18    | left_elbow
4     | left_ankle_pitch        | 19    | left_wrist_roll
5     | left_ankle_roll         | 20    | left_wrist_pitch
6     | right_hip_pitch         | 21    | left_wrist_yaw
7     | right_hip_roll          | 22    | right_shoulder_pitch
8     | right_hip_yaw           | 23    | right_shoulder_roll
9     | right_knee              | 24    | right_shoulder_yaw
10    | right_ankle_pitch       | 25    | right_elbow
11    | right_ankle_roll        | 26    | right_wrist_roll
12    | waist_yaw               | 27    | right_wrist_pitch
13    | waist_roll              | 28    | right_wrist_yaw
14    | waist_pitch             |       |
```

---

## 5. Input Data Formats

### 5.1 CSV Motion Format (Raw Input)

**Purpose**: Raw motion data for visualization and preprocessing.

**Columns**: 36 total

| Column Index | Data Type | Description |
|--------------|-----------|-------------|
| 0-2 | float | Base position (x, y, z) in world frame |
| 3-6 | float | Base orientation quaternion (x, y, z, w) |
| 7-35 | float | Joint positions in radians (29 joints) |

**Example Row**:
```csv
0.000545,-0.000051,0.782845,0.001066,0.031608,-0.059077,0.997752,-0.153094,0.195797,...
```

**Frame Rate**: Typically 30 FPS (from LAFAN dataset)

**Source**: [LAFAN1 Retargeting Dataset for G1](https://huggingface.co/datasets/lvhaidong/LAFAN1_Retargeting_Dataset/tree/main/g1)

### 5.2 NPZ Motion Format (Processed for Training)

**Purpose**: Preprocessed motion data stored in Weights & Biases registry.

**Keys**:

| Key | Shape | Description |
|-----|-------|-------------|
| `fps` | (1,) | Frame rate of the motion |
| `joint_pos` | (num_frames, 29) | Joint positions in radians |
| `joint_vel` | (num_frames, 29) | Joint velocities in rad/s |
| `body_pos_w` | (num_frames, 3) | Base position in world frame |
| `body_quat_w` | (num_frames, 4) | Base orientation quaternion (w, x, y, z) |
| `body_lin_vel_w` | (num_frames, 3) | Base linear velocity |
| `body_ang_vel_w` | (num_frames, 3) | Base angular velocity |

### 5.3 URDF/XML Robot Format

**Location**: 
- `robots/g1_ufb/g1_29dof_rev_1_0.urdf` - G1 URDF
- `src/mjlab/asset_zoo/robots/*/xmls/*.xml` - MuJoCo XML models

---

## 6. Available Commands & Scripts

### 6.1 Training Commands

```bash
# Train velocity tracking
uv run train Mjlab-Velocity-Flat-Unitree-G1 --env.scene.num-envs 4096

# Train motion imitation
uv run train Mjlab-Tracking-Flat-Unitree-G1 \
    --registry-name org/wandb-registry-Motions/motion_name \
    --env.scene.num-envs 8192 \
    --agent.max-iterations 2000

# Multi-GPU training
uv run train Mjlab-Velocity-Flat-Unitree-G1 --gpu-ids 0 1 --env.scene.num-envs 4096
```

### 6.2 Evaluation/Play Commands

```bash
# Play with trained policy from W&B
uv run play Mjlab-Tracking-Flat-Unitree-G1 --wandb-run-path org/project/run-id --num-envs 1

# Play with zero actions (sanity check)
uv run play Mjlab-Your-Task-Id --agent zero

# Play with random actions (sanity check)
uv run play Mjlab-Your-Task-Id --agent random

# Mac requires mjpython wrapper
uv run mjpython -m mjlab.scripts.play Mjlab-Tracking-Flat-Unitree-G1 --wandb-run-path run_path --num-envs 1
```

### 6.3 Motion Processing Commands

```bash
# Convert CSV to NPZ and upload to W&B registry
uv run python src/mjlab/scripts/csv_to_npz.py \
    --input_file motion.csv \
    --input_fps 30 \
    --output_name motion_name

# Visualize CSV motion in Rerun
python scripts/rerun_visualize.py --file_name data/fight1_subject2.csv
```

### 6.4 Utility Commands

```bash
# List all available environments
uv run list_envs

# Run demo
uv run demo

# Visualize NaN debugging
uv run viz-nan
```

---

## 7. Training Configuration Options

### 7.1 Environment Configuration

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--env.scene.num-envs` | Number of parallel environments | 4096, 8192 |
| `--env.episode-length-s` | Episode length in seconds | 10.0, 20.0 |
| `--env.decimation` | Physics steps per control step | 4 |

### 7.2 Agent/Training Configuration

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--agent.max-iterations` | Maximum training iterations | 2000 |
| `--agent.wandb-project` | W&B project name | "my-project" |
| `--registry-name` | Motion registry path | "org/wandb-registry-Motions/name" |
| `--gpu-ids` | GPU devices for multi-GPU | 0 1 |

### 7.3 Simulation Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `timestep` | Physics timestep | 0.005s |
| `iterations` | Solver iterations | 10 |
| `ls_iterations` | Line search iterations | 20 |

---

## 8. MDP Components (Modular Building Blocks)

### 8.1 Observations

Available observation functions in `mjlab.envs.mdp.observations`:

| Function | Description |
|----------|-------------|
| `joint_pos_rel` | Joint positions relative to default |
| `joint_vel_rel` | Joint velocities |
| `projected_gravity` | Gravity vector in body frame |
| `builtin_sensor` | IMU readings (lin_vel, ang_vel) |
| `last_action` | Previous action |
| `generated_commands` | Current command targets |
| `height_scan` | Terrain height from raycast |

### 8.2 Rewards

Available reward functions in `mjlab.envs.mdp.rewards` and task-specific modules:

| Function | Description |
|----------|-------------|
| `track_linear_velocity` | Track commanded linear velocity |
| `track_angular_velocity` | Track commanded angular velocity |
| `action_rate_l2` | Penalize action rate |
| `joint_pos_limits` | Penalize joint limit violations |
| `flat_orientation` | Reward upright posture |
| `feet_air_time` | Reward foot swing timing |
| `feet_slip` | Penalize foot slipping |
| `motion_*` | Motion tracking rewards (position, orientation, velocity) |

### 8.3 Terminations

| Function | Description |
|----------|-------------|
| `time_out` | Episode time limit |
| `bad_orientation` | Fell over (angle threshold) |
| `bad_anchor_pos` | Motion tracking position error |
| `bad_anchor_ori` | Motion tracking orientation error |
| `illegal_contact` | Unwanted collision |

### 8.4 Domain Randomization Events

| Function | Description |
|----------|-------------|
| `push_by_setting_velocity` | Apply external push |
| `reset_root_state_uniform` | Randomize initial pose |
| `reset_joints_by_offset` | Randomize initial joint positions |
| `geom_friction` | Randomize friction |
| `body_com_offset` | Randomize center of mass |
| `encoder_bias` | Randomize joint encoder bias |

---

## 9. Output Artifacts

### 9.1 Training Outputs

| Artifact | Location | Description |
|----------|----------|-------------|
| Checkpoints | W&B Files | Model weights (.pt files) |
| ONNX Policy | W&B Files | Deployable policy (.onnx) |
| Training Curves | W&B Dashboard | Reward, loss, metrics |
| Videos | W&B Media | Episode recordings |

### 9.2 Motion Processing Outputs

| Artifact | Location | Description |
|----------|----------|-------------|
| NPZ File | `/tmp/motion.npz` + W&B | Processed motion data |
| Video | `./motion.mp4` | Motion visualization |

---

## 10. Development Environment

### 10.1 Requirements

- **Python**: 3.10 - 3.13
- **GPU**: NVIDIA GPU with CUDA support (required for training)
- **OS**: Linux (training), macOS (evaluation only)

### 10.2 Setup Commands

```bash
# Install dependencies
uv sync

# Activate environment
source .venv/bin/activate

# Or on Nebius instance (pre-configured)
source .venv/bin/activate
```

### 10.3 Development Commands

```bash
make format     # Format and lint code
make type       # Type-check
make test-fast  # Run fast tests
make test       # Run full test suite
```

---

## 11. Integration Points

### 11.1 External Services

| Service | Purpose | Required For |
|---------|---------|--------------|
| **Weights & Biases** | Experiment tracking, model registry | Training, motion storage |
| **Rerun** | 3D visualization | Motion preview |

### 11.2 Data Pipeline

```
CSV Motion File (30 FPS)
        ↓
csv_to_npz.py (interpolate to 50 FPS, compute velocities)
        ↓
NPZ File → W&B Registry
        ↓
Training Script (loads from registry)
        ↓
Trained Policy (ONNX) → Real Robot Deployment
```

---

## 12. File Structure Summary

```
mjlab-hackathon/
├── src/mjlab/
│   ├── tasks/              # RL environments
│   │   ├── tracking/       # Motion imitation task
│   │   ├── velocity/       # Velocity tracking task
│   │   └── manipulation/   # Object manipulation task
│   ├── envs/               # Environment base classes
│   ├── managers/           # MDP component managers
│   ├── asset_zoo/          # Robot models (G1, Go1, YAM)
│   ├── terrains/           # Terrain generation
│   ├── sensor/             # Sensor implementations
│   ├── actuator/           # Actuator models
│   ├── scripts/            # CLI entry points
│   └── viewer/             # Visualization
├── scripts/
│   └── rerun_visualize.py  # Motion visualization
├── robots/
│   └── g1_ufb/             # G1 URDF and meshes
├── data/
│   └── fight1_subject2.csv # Sample motion file
└── docs/                   # Documentation
```

---

## 13. Quick Reference: Adding a New Policy

### For Motion Imitation (G1 Humanoid):

1. **Prepare motion CSV** (36 columns, LAFAN format)
2. **Visualize** (optional): `python scripts/rerun_visualize.py --file_name motion.csv`
3. **Convert to NPZ**: `uv run python src/mjlab/scripts/csv_to_npz.py --input_file motion.csv --output_name my_motion`
4. **Train**: `uv run train Mjlab-Tracking-Flat-Unitree-G1 --registry-name org/wandb-registry-Motions/my_motion --env.scene.num-envs 8192`
5. **Evaluate**: `uv run play Mjlab-Tracking-Flat-Unitree-G1 --wandb-run-path org/project/run-id`
6. **Deploy**: Download ONNX from W&B Files

### For Velocity Tracking (G1 or Go1):

1. **Train**: `uv run train Mjlab-Velocity-Flat-Unitree-G1 --env.scene.num-envs 4096`
2. **Evaluate**: `uv run play Mjlab-Velocity-Flat-Unitree-G1 --wandb-run-path run_path`
3. **Deploy**: Download ONNX from W&B Files

---

*This document is intended for planning agents to understand the repository capabilities before creating structured project plans.*
