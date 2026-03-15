"""Narrator module for the LLM demo layer.

This module generates natural language explanations and narration
for the judge-facing demo.
"""

import os
from typing import Optional

from fbx2robot.llm_demo.motion_catalog import MotionEntry, get_catalog


class DemoNarrator:
    """Generate narration and explanations for the demo."""

    def __init__(self, use_llm: bool = False):
        """Initialize narrator.

        Args:
            use_llm: Whether to use LLM for enhanced narration
        """
        self.use_llm = use_llm
        self._openai_client = None

    def _get_openai_client(self):
        """Lazy-load OpenAI client."""
        if self._openai_client is None:
            try:
                from openai import OpenAI

                api_key = os.environ.get("OPENAI_API_KEY")
                if api_key:
                    self._openai_client = OpenAI(api_key=api_key)
            except ImportError:
                pass
        return self._openai_client

    def introduce_project(self) -> str:
        """Generate project introduction."""
        intro = """
Welcome to FBX2Robot!

This project demonstrates an end-to-end pipeline that transforms 
standard animation files (FBX format) into trained robot motion policies.

The Pipeline:
1. FBX Animation File -> Blender extracts skeleton and motion data
2. Motion Retargeting -> Maps humanoid animation to Unitree G1 robot joints
3. Training Data -> Creates LAFAN-format CSV compatible with mjlab
4. Policy Training -> Trains motion imitation policy using reinforcement learning
5. Deployment -> Produces ONNX model for real robot execution

The G1 robot has 29 degrees of freedom, and our pipeline maps standard 
Mixamo humanoid animations to this joint space automatically.
""".strip()
        return intro

    def describe_motion(self, motion: MotionEntry) -> str:
        """Generate description for a motion."""
        description = f"Motion: {motion.display_name}\n"
        description += "-" * 40 + "\n"
        description += f"{motion.description}\n\n"

        description += "Technical Details:\n"
        if motion.num_frames > 0:
            description += f"  - Frames: {motion.num_frames}\n"
        if motion.duration_seconds > 0:
            description += f"  - Duration: {motion.duration_seconds:.2f} seconds\n"

        status_messages = {
            "trained": "This motion has a trained policy ready for playback.",
            "training": "This motion is currently being trained.",
            "ready": "This motion is processed and ready for training.",
            "pending": "This motion is waiting to be processed.",
        }
        description += f"\nStatus: {status_messages.get(motion.training_status, 'Unknown')}\n"

        if motion.wandb_run_path:
            description += f"\nTraining run: {motion.wandb_run_path}\n"

        return description

    def generate_playback_instructions(self, motion: MotionEntry) -> str:
        """Generate instructions for playing back a motion."""
        if motion.training_status != "trained" or not motion.wandb_run_path:
            return f"Motion '{motion.display_name}' is not yet trained or run path not available."

        instructions = f"""
To play the '{motion.display_name}' motion:

uv run play Mjlab-Tracking-Flat-Unitree-G1 \\
    --wandb-run-path {motion.wandb_run_path} \\
    --num-envs 1

This will:
1. Load the trained policy from Weights & Biases
2. Create a simulation environment with the G1 robot
3. Run the policy to execute the motion
4. Display visualization in your browser
""".strip()
        return instructions

    def summarize_results(self) -> str:
        """Generate summary of all motions and their status."""
        catalog = get_catalog()
        
        summary = "FBX2Robot Pipeline Results\n"
        summary += "=" * 40 + "\n\n"

        trained = catalog.list_trained_motions()
        available = catalog.list_available_motions()
        all_motions = catalog.list_motions()

        summary += f"Total Motions: {len(all_motions)}\n"
        summary += f"Processed: {len(available)}\n"
        summary += f"Trained: {len(trained)}\n\n"

        if trained:
            summary += "Trained Motions (Ready for Demo):\n"
            for m in trained:
                summary += f"  [OK] {m.display_name}\n"
                if m.quality_notes:
                    summary += f"       Quality: {m.quality_notes}\n"
            summary += "\n"

        pending = [m for m in all_motions if m.training_status == "pending"]
        if pending:
            summary += "Pending Motions:\n"
            for m in pending:
                summary += f"  [ ] {m.display_name}\n"

        return summary

    def answer_question(self, question: str) -> str:
        """Answer a question about the project using LLM if available."""
        if self.use_llm:
            client = self._get_openai_client()
            if client:
                return self._llm_answer(question)

        # Fallback to keyword-based answers
        return self._keyword_answer(question)

    def _keyword_answer(self, question: str) -> str:
        """Simple keyword-based Q&A."""
        question_lower = question.lower()

        if any(w in question_lower for w in ["what", "about", "explain", "project"]):
            return self.introduce_project()

        if any(w in question_lower for w in ["motion", "available", "list", "show"]):
            return get_catalog().get_summary()

        if any(w in question_lower for w in ["train", "result", "status"]):
            return self.summarize_results()

        if any(w in question_lower for w in ["play", "run", "execute", "demo"]):
            trained = get_catalog().list_trained_motions()
            if trained:
                return self.generate_playback_instructions(trained[0])
            return "No trained motions available yet."

        return (
            "I can help you with:\n"
            "- Information about the project ('What is this project?')\n"
            "- Available motions ('What motions are available?')\n"
            "- Training status ('What's the training status?')\n"
            "- Playback instructions ('How do I play a motion?')"
        )

    def _llm_answer(self, question: str) -> str:
        """Use LLM to answer question."""
        client = self._get_openai_client()
        if not client:
            return self._keyword_answer(question)

        try:
            catalog = get_catalog()
            context = f"""
You are explaining the FBX2Robot project, which converts FBX animation files 
into trained robot motion policies for the Unitree G1 humanoid robot.

Current status:
{self.summarize_results()}

Available commands:
- To play a motion: uv run play Mjlab-Tracking-Flat-Unitree-G1 --wandb-run-path <run_path>
- To process FBX: python scripts/process_fbx.py process <fbx_file>
- To train: uv run train Mjlab-Tracking-Flat-Unitree-G1 --registry-name <artifact>

Answer the user's question concisely and helpfully.
"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": question},
                ],
                max_tokens=300,
                temperature=0.7,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"LLM answer failed: {e}")
            return self._keyword_answer(question)


def get_narrator(use_llm: bool = False) -> DemoNarrator:
    """Get a demo narrator instance."""
    return DemoNarrator(use_llm=use_llm)
