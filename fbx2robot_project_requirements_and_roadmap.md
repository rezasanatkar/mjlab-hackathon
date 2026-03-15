# FBX2Robot Hackathon Project Requirements & Roadmap

## Project Name
**FBX2Robot: FBX Motion Ingestion, Retargeting, and Policy Training Pipeline for Unitree G1 in `mjlab-hackathon`**

---

## 1. Executive Summary

Build a code-first pipeline **inside the existing `mjlab-hackathon` repository** that:

1. Ingests humanoid animation `.fbx` files.
2. Extracts skeleton and animation data programmatically.
3. Retargets source motion into **Unitree G1 29-DOF** joint space.
4. Exports valid **mjlab-compatible 36-column LAFAN-style CSV** motion files.
5. Converts those CSVs into NPZ motion artifacts using the existing repo tooling.
6. Uploads motion artifacts to the W&B motion registry.
7. Trains motion imitation policies for **four target motions**.
8. Produces a lightweight **LLM-powered presentation/demo layer** for judges that explains, selects, and plays the trained motions.

This project must prioritize **end-to-end function**, **reproducibility**, and **hackathon demo readiness** over perfect motion realism.

---

## 2. Primary Goal

Create an end-to-end motion-to-policy pipeline that proves the following flow works:

**FBX animation -> extracted motion -> G1 retargeted motion -> CSV -> NPZ/W&B registry -> mjlab training -> policy playback -> judge-facing LLM demo**

---

## 3. Final Deliverables

The coding agent must produce the following by the end of the project:

### 3.1 Core Deliverables
- A new internal package named **`fbx2robot`** inside `mjlab-hackathon`
- A CLI pipeline that processes FBX motion files end-to-end
- A valid retargeted **robot motion CSV** for each of the four target motions
- W&B motion artifacts uploaded for each processed motion
- Trained or partially trained **G1 imitation policies** for each motion
- Playback/evaluation instructions for each trained run
- A minimal LLM layer for the final demo that lets judges select or describe a motion
- A short README for teammates/judges to run the pipeline and demo

### 3.2 Expected Target Motions
The following four motions must be supported:
1. `celebratory_gesture`
2. `short_dance_loop`
3. `sidestep_arm_sweep`
4. `bow_greeting`

### 3.3 Output Artifacts Per Motion
For each target motion, produce:
- `source.fbx`
- `canonical_motion.npz` or equivalent intermediate representation
- `robot_motion.csv`
- `metadata.json`
- optional `preview.mp4` or preview logs
- W&B registry artifact name
- training run path
- playback command
- best checkpoint/run summary

---

## 4. Required Constraints

### 4.1 Repository Constraint
- The project **must be implemented inside the existing `mjlab-hackathon` repo**.
- Do **not** create a separate top-level repo during the hackathon.
- Keep the new pipeline modular enough to be extracted later if desired.

### 4.2 Pipeline Constraint
- The pipeline must be **code-only** and reproducible.
- No manual Blender UI steps are allowed in the expected workflow.
- Blender may be used as a **headless backend** if needed.

### 4.3 Output Format Constraint
The final motion export used by `mjlab-hackathon` must match the required CSV layout:
- columns `0-2`: base position `(x, y, z)`
- columns `3-6`: base orientation quaternion
- columns `7-35`: 29 G1 joint angles in the repo’s expected order

### 4.4 Demo Constraint
- The final project must include a simple judge-facing demo layer.
- The demo layer must use an LLM only for **selection, explanation, or narration**, not as the low-level controller.
- The motion execution path must still go through the trained `mjlab` policies.

---

## 5. Non-Goals

The coding agent should explicitly avoid these unless the MVP is already complete:
- building a general-purpose humanoid foundation model
- solving generic manipulation tasks
- relying on real robot hardware for validation
- implementing a perfect physically realistic retargeter
- spending large amounts of time on web UI polish before core functionality works
- trying to train a single universal multi-skill policy before individual motions work

---

## 6. Project Architecture

### 6.1 End-to-End Flow

```text
FBX file
  -> FBX extraction backend
  -> canonical motion representation
  -> retargeting to G1 29-DOF
  -> mjlab-compatible motion CSV
  -> csv_to_npz.py
  -> W&B motion registry
  -> train Mjlab-Tracking-Flat-Unitree-G1
  -> play/evaluate trained run
  -> LLM-powered presentation/demo layer
```

### 6.2 Recommended Implementation Pattern
This project should mirror the **organizational style** of `video2robot-hackathon`, but live inside `mjlab-hackathon`.

---

## 7. Required Repository Changes

Create the following structure inside `mjlab-hackathon`:

```text
mjlab-hackathon/
├── fbx2robot/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   ├── pipeline.py
│   ├── fbx/
│   │   ├── loader.py
│   │   ├── blender_backend.py
│   │   ├── skeleton.py
│   │   └── normalize.py
│   ├── canonical/
│   │   ├── schema.py
│   │   ├── io.py
│   │   └── transforms.py
│   ├── retarget/
│   │   ├── mixamo_to_g1.py
│   │   ├── constraints.py
│   │   ├── root_motion.py
│   │   └── validation.py
│   ├── export/
│   │   ├── motion_csv.py
│   │   ├── metadata.py
│   │   └── preview.py
│   └── llm_demo/
│       ├── motion_catalog.py
│       ├── prompt_router.py
│       └── narrator.py
├── scripts/
│   ├── process_fbx.py
│   ├── preview_fbx_motion.py
│   ├── train_motion_from_csv.sh
│   ├── run_motion_suite.py
│   ├── run_demo.py
│   └── find_blender.py
├── data/
│   └── motions/
│       ├── celebratory_gesture/
│       ├── short_dance_loop/
│       ├── sidestep_arm_sweep/
│       └── bow_greeting/
└── docs/
    └── FBX2ROBOT.md
```

---

## 8. Environment & Tooling Requirements

### 8.1 Assumptions
The environment already has:
- `mjlab-hackathon` checked out
- CUDA installed
- WSL installed
- Weights & Biases account/API key available
- `uv` / repository virtual environment available
- access to the four FBX motion files

### 8.2 Blender Requirement
The coding agent must locate Blender or install a usable headless backend.

#### Step 1: Try to discover Blender automatically
The agent must search common Windows paths from WSL, such as:
- `/mnt/c/Program Files/Blender Foundation/`
- `/mnt/c/Program Files (x86)/Blender Foundation/`
- user-local installs if necessary

The agent should implement `scripts/find_blender.py` that:
- searches common install paths
- optionally invokes `powershell.exe -Command "Get-Command blender"`
- checks candidate executables
- verifies headless execution with:
  - `blender.exe -b --version`

#### Step 2: If Blender is not found
If no usable Blender install is found, the agent should:
- document the failure clearly
- install Blender in a reproducible way if permitted
- prefer a headless/scripted installation path
- record the resolved executable path in config

### 8.3 Python Dependencies
The agent must install any missing packages needed for:
- numerical ops
- rotation math
- data serialization
- optional visualization
- LLM demo glue

Recommended likely dependencies:
- `numpy`
- `scipy`
- `pandas`
- `typer` or `argparse`
- `pydantic` or dataclasses-based schema layer
- `matplotlib` only if needed for quick debugging plots

The agent must keep dependency additions minimal and document them.

---

## 9. Data Contracts

### 9.1 Canonical Intermediate Motion Representation
Before retargeting to G1, define a canonical internal format.

At minimum it must include:
- `fps`
- `num_frames`
- `root_pos` shape `(N, 3)`
- `root_quat_xyzw` shape `(N, 4)`
- `joint_names`
- `joint_rotations` for source humanoid joints
- optional per-frame metadata

This intermediate representation must be serializable to `.npz` or `.json + npz`.

### 9.2 G1 Joint Order
The exported robot motion must follow the G1 joint order already used by the repo:
1. `left_hip_pitch`
2. `left_hip_roll`
3. `left_hip_yaw`
4. `left_knee`
5. `left_ankle_pitch`
6. `left_ankle_roll`
7. `right_hip_pitch`
8. `right_hip_roll`
9. `right_hip_yaw`
10. `right_knee`
11. `right_ankle_pitch`
12. `right_ankle_roll`
13. `waist_yaw`
14. `waist_roll`
15. `waist_pitch`
16. `left_shoulder_pitch`
17. `left_shoulder_roll`
18. `left_shoulder_yaw`
19. `left_elbow`
20. `left_wrist_roll`
21. `left_wrist_pitch`
22. `left_wrist_yaw`
23. `right_shoulder_pitch`
24. `right_shoulder_roll`
25. `right_shoulder_yaw`
26. `right_elbow`
27. `right_wrist_roll`
28. `right_wrist_pitch`
29. `right_wrist_yaw`

### 9.3 Motion CSV Export Contract
Each row must contain exactly 36 values:
- 3 base position values
- 4 base quaternion values
- 29 joint angles

The export must pass validation checks before downstream training.

---

## 10. Retargeting Requirements

### 10.1 Source Assumption
The source FBX animations are humanoid motions, likely Mixamo-style or similar.

### 10.2 Retargeting Requirements
The coding agent must implement a retargeter that:
- maps source joints to G1-equivalent joints
- normalizes handedness / axes / root orientation
- computes reasonable base motion
- clamps or regularizes unreasonable joint angles
- handles missing joints gracefully when possible
- produces stable, training-usable output over physically perfect output

### 10.3 Motion Quality Rules
The retargeter should include safeguards for:
- NaNs
- impossible quaternion values
- obvious frame discontinuities
- extreme velocity spikes
- joint-angle blowups
- duplicated or zero-length animation ranges

### 10.4 Smoothing / Cleanup
The agent may apply lightweight post-processing such as:
- quaternion normalization
- frame interpolation
- temporal smoothing
- start/end stabilization padding
- root drift cleanup

The agent must keep these modifications documented.

---

## 11. CLI Requirements

### 11.1 Primary Command
The following style of command must work:

```bash
python scripts/process_fbx.py \
  --input data/motions/bow_greeting/source.fbx \
  --output-dir data/motions/bow_greeting \
  --motion-name bow_greeting
```

### 11.2 Required CLI Behavior
The CLI must:
- validate input path
- discover/configure Blender backend if required
- extract source motion
- create canonical intermediate artifact
- retarget to G1
- export `robot_motion.csv`
- emit `metadata.json`
- optionally create a preview artifact
- fail with actionable error messages

### 11.3 Batch Command
A batch script must run the full suite for all four motions.

Example target:

```bash
python scripts/run_motion_suite.py
```

This should process:
- `celebratory_gesture`
- `short_dance_loop`
- `sidestep_arm_sweep`
- `bow_greeting`

---

## 12. Training Integration Requirements

The coding agent must integrate directly with the existing `mjlab-hackathon` flow.

### 12.1 CSV to NPZ Conversion
For each successful motion CSV, run:

```bash
uv run python src/mjlab/scripts/csv_to_npz.py \
  --input_file <motion_csv> \
  --input_fps 30 \
  --output_name <motion_name>
```

### 12.2 Training Command Template
For each motion, the agent must produce and run a training command of the form:

```bash
uv run train Mjlab-Tracking-Flat-Unitree-G1 \
  --registry-name <org>/wandb-registry-Motions/<motion_name> \
  --env.scene.num-envs 4096 \
  --agent.wandb-project fbx2robot-hackathon \
  --agent.max-iterations 1000
```

Use lower iteration counts first for smoke tests. Increase only after the pipeline is stable.

### 12.3 Evaluation Command Template
The agent must record the playback command for each successful run:

```bash
uv run play Mjlab-Tracking-Flat-Unitree-G1 \
  --wandb-run-path <run_path> \
  --num-envs 1
```

---

## 13. Motion Processing Order

The coding agent must process the motions in this order:

1. `bow_greeting`
2. `celebratory_gesture`
3. `sidestep_arm_sweep`
4. `short_dance_loop`

Rationale:
- `bow_greeting` is likely the easiest grounded motion
- `celebratory_gesture` is expressive but still manageable
- `sidestep_arm_sweep` adds lateral motion complexity
- `short_dance_loop` is the most complex of the initial set

Do not start with the most complex motion first.

---

## 14. Step-by-Step Roadmap

## Phase 0 — Setup and repo audit

### Objectives
- confirm environment health
- confirm repo commands work
- confirm W&B access
- confirm Blender availability or install plan

### Tasks
1. activate environment and verify `mjlab-hackathon` basics
2. run a basic repo smoke test such as listing envs
3. verify W&B login status
4. implement Blender discovery script
5. test Blender headless invocation
6. add any missing dependencies
7. create initial folder structure

### Acceptance Criteria
- environment is operational
- Blender executable path resolved or installed path documented
- new `fbx2robot` package skeleton created

---

## Phase 1 — FBX ingestion backend

### Objectives
- load FBX without manual UI steps
- extract animation and skeleton data reproducibly

### Tasks
1. implement `fbx2robot/fbx/blender_backend.py`
2. create a headless Blender script that imports FBX and dumps animation data
3. support extraction of:
   - frame count
n   - FPS
   - skeleton hierarchy
   - per-frame root transform
   - per-frame bone transforms/rotations
4. serialize extracted motion to canonical artifact
5. validate extraction on one motion

### Acceptance Criteria
- one source FBX can be parsed programmatically
- canonical artifact is saved to disk
- extracted motion has expected frame count and joint naming info

---

## Phase 2 — Canonical motion representation

### Objectives
- define a stable interface between extraction and retargeting

### Tasks
1. implement `canonical/schema.py`
2. implement canonical artifact save/load helpers
3. normalize:
   - frame rate
   - coordinate system
   - quaternion conventions
4. create validation routines

### Acceptance Criteria
- canonical motion can be saved/loaded independently of FBX
- validation detects malformed data early

---

## Phase 3 — Retarget Mixamo-style humanoid motion to G1

### Objectives
- convert source motion into G1 joint space

### Tasks
1. implement `retarget/mixamo_to_g1.py`
2. define source-joint to G1 mapping
3. implement root motion handling
4. implement joint constraints and clipping
5. create angle sanity checks
6. export first draft retargeted motion arrays

### Acceptance Criteria
- one motion produces G1-aligned joint trajectories with correct DOF count
- output has no NaNs or shape mismatches

---

## Phase 4 — Export mjlab-compatible motion CSV

### Objectives
- generate valid 36-column CSV for existing repo tooling

### Tasks
1. implement `export/motion_csv.py`
2. write CSV headerless format expected by current repo tooling
3. implement validation:
   - 36 columns exactly
   - valid quaternions
   - frame count > 0
   - no NaNs
4. generate `metadata.json`
5. optionally create simple preview or diagnostics

### Acceptance Criteria
- `robot_motion.csv` is created successfully
- the existing visualization path can inspect the result if useful
- the output is accepted by downstream conversion tools

---

## Phase 5 — Integrate with `csv_to_npz.py`

### Objectives
- prove compatibility with existing motion preprocessing flow

### Tasks
1. run `csv_to_npz.py` on the generated CSV
2. confirm NPZ artifact generation
3. confirm upload to W&B motion registry
4. record artifact names

### Acceptance Criteria
- first motion becomes a valid W&B motion artifact usable by `Mjlab-Tracking-Flat-Unitree-G1`

---

## Phase 6 — Train first imitation policy

### Objectives
- prove the motion artifact can drive training

### Tasks
1. train `bow_greeting` first using conservative settings
2. monitor for crashes or invalid motion behavior
3. record run path
4. evaluate with `play`
5. capture notes on imitation quality and failure modes

### Acceptance Criteria
- one training run launches successfully
- one evaluation/playback command works
- a basic demo clip or live playback is available

---

## Phase 7 — Scale to remaining motions

### Objectives
- apply stable pipeline to the other three motions

### Tasks
1. process `celebratory_gesture`
2. process `sidestep_arm_sweep`
3. process `short_dance_loop`
4. train each motion
5. rank outputs by stability and demo quality

### Acceptance Criteria
- all four motions have completed the ingestion/export path
- at least two motions have convincing training/playback
- all run paths and artifact names are documented

---

## Phase 8 — Build judge-facing LLM demo layer

### Objectives
- create a lightweight final presentation interface for judges

### Required Behavior
The LLM layer should:
- describe the project in plain language
- let users select one of the four motions
- optionally map natural prompts to the closest motion
- explain what the model is about to do
- print or trigger the correct playback command/run selection
- summarize quality tradeoffs in simple terms

### Tasks
1. create a tiny motion catalog
2. implement prompt routing such as:
   - “make the robot greet us” -> `bow_greeting`
   - “show something celebratory” -> `celebratory_gesture`
   - “show a movement with stepping” -> `sidestep_arm_sweep`
   - “show the dance” -> `short_dance_loop`
3. implement narration text based on metadata
4. optionally include W&B links or run summaries

### Acceptance Criteria
- one command can launch or guide the judge demo
- LLM behavior is helpful but not mission-critical to policy execution

---

## 15. Testing Requirements

### 15.1 Smoke Tests
The coding agent must create fast smoke tests for:
- Blender discovery
- FBX extraction on a single short file
- canonical save/load roundtrip
- retarget output shape checks
- CSV export validity

### 15.2 Functional Validation
For each motion, verify:
- CSV has correct shape
- quaternions are normalized or close enough
- joint count is 29
- `csv_to_npz.py` succeeds
- training launches without immediate failure

### 15.3 Failure Reporting
If any step fails, the pipeline must fail with:
- the motion name
- the failed stage
- the reason
- suggested next debugging step

---

## 16. Logging & Metadata Requirements

Each motion directory must include `metadata.json` with at least:
- `motion_name`
- `source_file`
- `source_fps`
- `num_frames`
- `blender_path_used`
- `processing_timestamp`
- `retarget_version`
- `csv_path`
- `wandb_motion_artifact`
- `wandb_training_run`
- `notes`

The agent should also keep a top-level run summary file, for example:
- `data/motions/summary.json`

---

## 17. Performance Guidance

### Initial training settings
Use modest settings for the first end-to-end proof:
- `--env.scene.num-envs 2048` or `4096`
- `--agent.max-iterations 300-1000`

Only scale up once the pipeline is stable.

### Processing Guidance
- prefer short clips first
- trim or pad clips if needed
- keep motion sequences stable and judge-friendly

---

## 18. Judge Demo Requirements

The final hackathon presentation should demonstrate:

1. **Input**: source FBX motion files
2. **Pipeline**: extracted and retargeted robot motion artifacts
3. **Training**: evidence that `mjlab` is training on those motions
4. **Playback**: best trained policies running in simulation
5. **LLM Layer**: a simple natural-language interface that selects/explains motions

### Demo script target
The final demo should ideally let a judge do something like:
- “Show the greeting motion”
- “Show something more celebratory”
- “Which motions trained best?”

And receive:
- a short explanation
- the selected motion/run
- the resulting playback or instructions to launch it

---

## 19. Definition of Done

The project is considered complete when all of the following are true:

1. `fbx2robot` exists inside `mjlab-hackathon`
2. Blender or equivalent backend is discovered and runs headless
3. At least one FBX motion can be processed end-to-end automatically
4. All four target motions can be exported to valid robot motion CSVs
5. At least one motion completes the full CSV -> NPZ -> training -> playback loop
6. Preferably two or more motions show convincing playback quality
7. The team has a reproducible command path for rerunning the full pipeline
8. The judge demo includes an LLM presentation layer
9. Documentation exists for teammates to run the pipeline quickly

---

## 20. Immediate First Actions for the Coding Agent

Execute the following in order:

1. audit current repo state and confirm environment health
2. create the `fbx2robot` package skeleton and scripts listed above
3. implement Blender discovery and headless smoke test
4. wire a minimal FBX extraction path for `bow_greeting`
5. define canonical motion schema and persist one extracted artifact
6. implement first-pass Mixamo-to-G1 retargeter
7. export first valid `robot_motion.csv`
8. run `csv_to_npz.py` on that CSV
9. launch first `Mjlab-Tracking-Flat-Unitree-G1` run
10. capture results, iterate, then scale to the other three motions

---

## 21. Agent Prompt to Start Implementation

Use the following as the implementation brief:

> Build an internal package named `fbx2robot` inside the existing `mjlab-hackathon` repository. The goal is to ingest humanoid `.fbx` animation files, extract motion data through a reproducible code-only pipeline, retarget the motion into the Unitree G1 29-DOF joint space, export a valid 36-column mjlab-compatible motion CSV, convert that CSV into a W&B motion artifact using the existing `csv_to_npz.py` flow, and train motion-imitation policies with `Mjlab-Tracking-Flat-Unitree-G1`. The four target motions are `celebratory_gesture`, `short_dance_loop`, `sidestep_arm_sweep`, and `bow_greeting`. Start with `bow_greeting` first. Use Blender in headless mode if necessary, but do not require manual Blender UI steps. Prioritize end-to-end pipeline correctness, reproducibility, validation, and demo readiness over perfect retargeting realism. After the motion pipeline works, add a minimal LLM demo layer that selects and explains the trained motions for judges.

