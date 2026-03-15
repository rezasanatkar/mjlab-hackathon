"""Command-line interface for FBX2Robot pipeline."""

import argparse
from pathlib import Path
from typing import Optional

from fbx2robot.config import get_config, BLENDER_PATH, MIXAMO_DIR, MOTIONS_DIR
from fbx2robot.pipeline import process_fbx, process_all_motions


def cmd_process(args):
    """Process a single FBX file."""
    result = process_fbx(
        fbx_path=args.input,
        motion_name=args.motion_name,
        output_dir=args.output_dir,
        scale_factor=args.scale,
        apply_limits=not args.no_limits,
        smooth_window=args.smooth,
    )

    if result.success:
        print(f"\nOutputs:")
        print(f"  CSV: {result.csv_path}")
        print(f"  Metadata: {result.metadata_path}")
        if result.canonical_path:
            print(f"  Canonical: {result.canonical_path}")
    else:
        print(f"\nFailed: {result.error}")
        return 1

    return 0


def cmd_process_all(args):
    """Process all FBX files in Mixamo directory."""
    results = process_all_motions()

    successes = sum(1 for r in results.values() if r.success)
    if successes < len(results):
        return 1
    return 0


def cmd_validate(args):
    """Validate a CSV file."""
    from fbx2robot.export.motion_csv import validate_csv

    csv_path = Path(args.csv)
    is_valid, issues = validate_csv(csv_path)

    if is_valid:
        print(f"[OK] {csv_path} is valid")
        return 0
    else:
        print(f"[X] {csv_path} has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return 1


def cmd_info(args):
    """Show configuration info."""
    config = get_config()

    print("FBX2Robot Configuration")
    print("=" * 40)
    print(f"Blender path: {BLENDER_PATH}")
    print(f"  Exists: {BLENDER_PATH.exists()}")
    print(f"Mixamo directory: {MIXAMO_DIR}")
    print(f"  Exists: {MIXAMO_DIR.exists()}")
    if MIXAMO_DIR.exists():
        fbx_files = list(MIXAMO_DIR.glob("*.fbx"))
        print(f"  FBX files: {len(fbx_files)}")
        for f in fbx_files:
            print(f"    - {f.name}")
    print(f"Motions directory: {MOTIONS_DIR}")
    print(f"  Exists: {MOTIONS_DIR.exists()}")

    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="FBX2Robot: FBX Motion Ingestion and Retargeting Pipeline"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Process command
    process_parser = subparsers.add_parser("process", help="Process a single FBX file")
    process_parser.add_argument("input", type=Path, help="Input FBX file")
    process_parser.add_argument(
        "--motion-name", "-n", type=str, help="Motion name (defaults to filename)"
    )
    process_parser.add_argument(
        "--output-dir", "-o", type=Path, help="Output directory"
    )
    process_parser.add_argument(
        "--scale", "-s", type=float, default=1.0, help="Position scale factor"
    )
    process_parser.add_argument(
        "--smooth", type=int, default=3, help="Smoothing window size (0 to disable)"
    )
    process_parser.add_argument(
        "--no-limits", action="store_true", help="Don't apply joint limits"
    )
    process_parser.set_defaults(func=cmd_process)

    # Process all command
    all_parser = subparsers.add_parser(
        "process-all", help="Process all FBX files in Mixamo directory"
    )
    all_parser.set_defaults(func=cmd_process_all)

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a CSV file")
    validate_parser.add_argument("csv", type=Path, help="CSV file to validate")
    validate_parser.set_defaults(func=cmd_validate)

    # Info command
    info_parser = subparsers.add_parser("info", help="Show configuration info")
    info_parser.set_defaults(func=cmd_info)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    exit(main())
