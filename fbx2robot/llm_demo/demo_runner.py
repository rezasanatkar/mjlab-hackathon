"""Demo runner for the LLM demo layer.

This is the main entry point for the judge-facing demo that ties
together motion selection, playback, and narration.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from fbx2robot.config import Config
from fbx2robot.llm_demo.motion_catalog import MotionCatalog, get_catalog
from fbx2robot.llm_demo.prompt_router import PromptRouter, route_prompt
from fbx2robot.llm_demo.narrator import DemoNarrator, get_narrator


class DemoRunner:
    """Main demo runner for FBX2Robot."""

    def __init__(self, use_llm: bool = False, config: Optional[Config] = None):
        """Initialize demo runner.

        Args:
            use_llm: Whether to use LLM for enhanced interactions
            config: Optional configuration
        """
        self.config = config or Config()
        self.use_llm = use_llm
        self.catalog = get_catalog()
        self.router = PromptRouter(catalog=self.catalog, use_llm=use_llm)
        self.narrator = get_narrator(use_llm=use_llm)

        # Set API key if available in config
        if self.config.openai_api_key:
            os.environ["OPENAI_API_KEY"] = self.config.openai_api_key

    def run_interactive(self):
        """Run interactive demo session."""
        print("\n" + "=" * 60)
        print("FBX2Robot Interactive Demo")
        print("=" * 60)
        print()
        print(self.narrator.introduce_project())
        print()
        print("-" * 60)
        print("Available commands:")
        print("  'list'     - Show available motions")
        print("  'status'   - Show training status")
        print("  'play X'   - Play motion X")
        print("  'ask X'    - Ask a question")
        print("  'quit'     - Exit demo")
        print("-" * 60)
        print()
        print("Or just describe what you want to see!")
        print()

        while True:
            try:
                user_input = input(">>> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if not user_input:
                continue

            if user_input.lower() == "quit":
                print("Goodbye!")
                break

            response = self.process_input(user_input)
            print()
            print(response)
            print()

    def process_input(self, user_input: str) -> str:
        """Process user input and return response.

        Args:
            user_input: User's input string

        Returns:
            Response string
        """
        input_lower = user_input.lower().strip()

        # Handle explicit commands
        if input_lower == "list":
            return self.catalog.get_summary()

        if input_lower == "status":
            return self.narrator.summarize_results()

        if input_lower.startswith("play "):
            motion_name = user_input[5:].strip()
            return self.play_motion_by_name(motion_name)

        if input_lower.startswith("ask "):
            question = user_input[4:].strip()
            return self.narrator.answer_question(question)

        # Otherwise, try to route the natural language input to a motion
        result = self.router.route(user_input)

        if result.matched_motion:
            response = result.explanation + "\n\n"

            if result.matched_motion.training_status == "trained":
                response += "Would you like me to play this motion? (say 'play' to continue)\n"
            else:
                response += f"This motion is currently '{result.matched_motion.training_status}'.\n"

            if result.alternatives:
                response += "\nAlternatives:\n"
                for alt in result.alternatives:
                    response += f"  - {alt.display_name}\n"

            return response
        else:
            return result.explanation

    def play_motion_by_name(self, name_or_query: str) -> str:
        """Play a motion by name or search query.

        Args:
            name_or_query: Motion name or search query

        Returns:
            Response string
        """
        # First try direct name lookup
        motion = self.catalog.get_motion(name_or_query)

        # If not found, try searching
        if not motion:
            result = self.router.route(name_or_query)
            motion = result.matched_motion

        if not motion:
            return f"Could not find motion '{name_or_query}'.\n\n{self.catalog.get_summary()}"

        if motion.training_status != "trained":
            return (
                f"Motion '{motion.display_name}' is not trained yet "
                f"(status: {motion.training_status}).\n"
                f"Train it first with:\n"
                f"  uv run train Mjlab-Tracking-Flat-Unitree-G1 --registry-name <artifact>"
            )

        if not motion.wandb_run_path:
            return f"Motion '{motion.display_name}' has no W&B run path recorded."

        return self._execute_playback(motion)

    def _execute_playback(self, motion) -> str:
        """Execute motion playback command.

        Args:
            motion: MotionEntry to play

        Returns:
            Response string
        """
        cmd = [
            "uv",
            "run",
            "play",
            "Mjlab-Tracking-Flat-Unitree-G1",
            "--wandb-run-path",
            motion.wandb_run_path,
            "--num-envs",
            "1",
        ]

        print(f"\nExecuting: {' '.join(cmd)}")
        print("Starting playback...")

        try:
            # For demo purposes, we'll print the command but not block
            result = subprocess.run(
                cmd,
                cwd=Path(__file__).parent.parent.parent,
                capture_output=False,
                timeout=300,  # 5 minute timeout
            )
            if result.returncode == 0:
                return f"Playback of '{motion.display_name}' completed."
            else:
                return f"Playback failed with code {result.returncode}"
        except subprocess.TimeoutExpired:
            return "Playback timed out."
        except FileNotFoundError:
            return (
                "Could not find 'uv' command. Make sure you're in the right environment.\n"
                f"Manual command:\n{' '.join(cmd)}"
            )
        except Exception as e:
            return f"Playback failed: {e}"

    def get_demo_script(self) -> str:
        """Generate a demo script for judges."""
        script = """
FBX2Robot Demo Script
=====================

This demo shows the complete pipeline from FBX animation to robot motion.

PART 1: Introduction
--------------------
"Welcome to FBX2Robot! This project transforms standard animation files 
into trained robot motion policies for the Unitree G1 humanoid robot."

PART 2: Pipeline Overview  
-------------------------
Show the pipeline flow:
1. Import FBX file from Mixamo
2. Extract skeleton and animation data via Blender
3. Retarget to G1's 29-DOF joint space
4. Generate training data in LAFAN CSV format
5. Train motion imitation policy
6. Export ONNX for deployment

PART 3: Motion Selection (Interactive)
--------------------------------------
"Let's see the robot greet us with a bow."
>>> show me a greeting

"How about something more celebratory?"
>>> show me a celebration

PART 4: Playback
----------------
>>> play bow_greeting

PART 5: Q&A
-----------
"Any questions about the project?"

Key talking points:
- Automatic bone mapping from Mixamo to G1
- GPU-accelerated training with 4096 parallel environments
- ~10-15 minute training time per motion
- Supports any Mixamo-compatible humanoid animation
""".strip()
        return script


def main():
    """Main entry point for demo."""
    import argparse

    parser = argparse.ArgumentParser(description="FBX2Robot Demo")
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Enable LLM-enhanced interactions",
    )
    parser.add_argument(
        "--script",
        action="store_true",
        help="Print demo script instead of running interactive",
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Process a single query and exit",
    )
    args = parser.parse_args()

    runner = DemoRunner(use_llm=args.use_llm)

    if args.script:
        print(runner.get_demo_script())
    elif args.query:
        print(runner.process_input(args.query))
    else:
        runner.run_interactive()


if __name__ == "__main__":
    main()
