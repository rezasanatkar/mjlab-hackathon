"""Blender script for FBX extraction.

This script is executed by Blender in headless mode.
Usage: blender -b -P blender_script.py -- <fbx_path> <output_path>
"""

import sys
import json
import math
from pathlib import Path

import bpy
import mathutils
import numpy as np


def clear_scene():
    """Clear the current Blender scene."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def import_fbx(fbx_path: str) -> bool:
    """Import FBX file into Blender."""
    try:
        bpy.ops.import_scene.fbx(
            filepath=fbx_path,
            use_anim=True,
            ignore_leaf_bones=False,
            automatic_bone_orientation=True,
        )
        return True
    except Exception as e:
        print(f"Error importing FBX: {e}")
        return False


def find_armature():
    """Find the armature object in the scene."""
    for obj in bpy.context.scene.objects:
        if obj.type == "ARMATURE":
            return obj
    return None


def get_animation_range(armature):
    """Get the animation frame range."""
    if armature.animation_data and armature.animation_data.action:
        action = armature.animation_data.action
        return int(action.frame_range[0]), int(action.frame_range[1])
    return bpy.context.scene.frame_start, bpy.context.scene.frame_end


def quaternion_to_array(quat: mathutils.Quaternion) -> list:
    """Convert Blender quaternion to list [w, x, y, z]."""
    return [quat.w, quat.x, quat.y, quat.z]


def vector_to_array(vec: mathutils.Vector) -> list:
    """Convert Blender vector to list."""
    return [vec.x, vec.y, vec.z]


def extract_motion_data(armature, frame_start: int, frame_end: int) -> dict:
    """Extract motion data from armature for all frames."""
    fps = bpy.context.scene.render.fps
    bone_names = [bone.name for bone in armature.pose.bones]

    # Build hierarchy
    hierarchy = {}
    for bone in armature.pose.bones:
        if bone.parent:
            hierarchy[bone.name] = bone.parent.name
        else:
            hierarchy[bone.name] = None

    frames_data = []

    for frame in range(frame_start, frame_end + 1):
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()

        frame_data = {
            "frame_index": frame - frame_start,
            "timestamp": (frame - frame_start) / fps,
        }

        # Find root bone (usually Hips)
        root_bone = None
        for bone in armature.pose.bones:
            if bone.parent is None or "hip" in bone.name.lower():
                root_bone = bone
                break

        if root_bone is None:
            root_bone = armature.pose.bones[0]

        # Get root world transform
        root_matrix = armature.matrix_world @ root_bone.matrix
        root_pos = root_matrix.to_translation()
        root_rot = root_matrix.to_quaternion()

        frame_data["root_position"] = vector_to_array(root_pos)
        frame_data["root_rotation"] = quaternion_to_array(root_rot)

        # Get bone rotations (local space)
        bone_rotations = {}
        for bone in armature.pose.bones:
            # Get local rotation relative to rest pose
            if bone.rotation_mode == "QUATERNION":
                rot = bone.rotation_quaternion
            else:
                rot = bone.rotation_euler.to_quaternion()

            bone_rotations[bone.name] = quaternion_to_array(rot)

        frame_data["bone_rotations"] = bone_rotations
        frames_data.append(frame_data)

    return {
        "fps": fps,
        "num_frames": len(frames_data),
        "bone_names": bone_names,
        "bone_hierarchy": hierarchy,
        "frames": frames_data,
    }


def main():
    """Main extraction function."""
    # Parse command line arguments
    argv = sys.argv
    if "--" in argv:
        args = argv[argv.index("--") + 1 :]
    else:
        print("Error: Missing arguments. Usage: blender -b -P script.py -- <fbx> <out>")
        sys.exit(1)

    if len(args) < 2:
        print("Error: Need FBX path and output path")
        sys.exit(1)

    fbx_path = args[0]
    output_path = args[1]

    print(f"Processing: {fbx_path}")
    print(f"Output: {output_path}")

    # Clear scene and import FBX
    clear_scene()
    if not import_fbx(fbx_path):
        sys.exit(1)

    # Find armature
    armature = find_armature()
    if armature is None:
        print("Error: No armature found in FBX")
        sys.exit(1)

    print(f"Found armature: {armature.name}")
    print(f"Bones: {len(armature.pose.bones)}")

    # Get animation range
    frame_start, frame_end = get_animation_range(armature)
    print(f"Animation range: {frame_start} - {frame_end}")

    # Extract motion data
    motion_data = extract_motion_data(armature, frame_start, frame_end)
    motion_data["source_file"] = fbx_path

    # Save to JSON
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(motion_data, f, indent=2)

    print(f"Extracted {motion_data['num_frames']} frames at {motion_data['fps']} FPS")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()
