"""LLM Demo Layer for FBX2Robot.

This module provides the judge-facing demo interface that combines
natural language understanding with motion selection and playback.
"""

from fbx2robot.llm_demo.motion_catalog import MotionCatalog, MotionEntry, get_catalog
from fbx2robot.llm_demo.prompt_router import PromptRouter, route_prompt, RoutingResult
from fbx2robot.llm_demo.narrator import DemoNarrator, get_narrator
from fbx2robot.llm_demo.demo_runner import DemoRunner
from fbx2robot.llm_demo.conversation import ConversationManager, ConversationState, Message

__all__ = [
    "MotionCatalog",
    "MotionEntry",
    "get_catalog",
    "PromptRouter",
    "route_prompt",
    "RoutingResult",
    "DemoNarrator",
    "get_narrator",
    "DemoRunner",
    "ConversationManager",
    "ConversationState",
    "Message",
]
