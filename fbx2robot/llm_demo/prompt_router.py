"""Prompt router for the LLM demo layer.

This module routes natural language prompts to appropriate motions
using keyword matching and optional LLM enhancement.
"""

import os
from typing import List, Optional, Tuple
from dataclasses import dataclass

from fbx2robot.llm_demo.motion_catalog import MotionCatalog, MotionEntry, get_catalog


@dataclass
class RoutingResult:
    """Result of routing a prompt to a motion."""

    query: str
    matched_motion: Optional[MotionEntry]
    confidence: float  # 0.0 to 1.0
    explanation: str
    alternatives: List[MotionEntry]


class PromptRouter:
    """Routes natural language prompts to motions."""

    def __init__(self, catalog: Optional[MotionCatalog] = None, use_llm: bool = False):
        """Initialize router.

        Args:
            catalog: Motion catalog to use
            use_llm: Whether to use LLM for enhanced routing
        """
        self.catalog = catalog or get_catalog()
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
                print("Warning: openai package not installed")
        return self._openai_client

    def route(self, query: str) -> RoutingResult:
        """Route a natural language query to a motion.

        Args:
            query: Natural language query (e.g., "show me a greeting")

        Returns:
            RoutingResult with matched motion and explanation
        """
        query_lower = query.lower().strip()

        # First try keyword matching
        keyword_results = self._keyword_match(query_lower)

        if keyword_results:
            best_match = keyword_results[0]
            alternatives = keyword_results[1:3]  # Top 3 alternatives

            # Calculate confidence based on match quality
            confidence = self._calculate_confidence(query_lower, best_match)

            explanation = self._generate_explanation(query, best_match, confidence)

            return RoutingResult(
                query=query,
                matched_motion=best_match,
                confidence=confidence,
                explanation=explanation,
                alternatives=alternatives,
            )

        # If no keyword match and LLM is enabled, try LLM routing
        if self.use_llm:
            llm_result = self._llm_route(query)
            if llm_result:
                return llm_result

        # No match found
        return RoutingResult(
            query=query,
            matched_motion=None,
            confidence=0.0,
            explanation=f"I couldn't find a motion matching '{query}'. "
            f"Available motions: {', '.join(m.display_name for m in self.catalog.list_motions())}",
            alternatives=self.catalog.list_motions()[:3],
        )

    def _keyword_match(self, query: str) -> List[MotionEntry]:
        """Match query against motion keywords."""
        scores = []

        for motion in self.catalog.list_motions():
            score = 0

            # Exact name match
            if motion.name in query or query in motion.name:
                score += 10

            # Display name match
            if motion.display_name.lower() in query:
                score += 8

            # Keyword matches
            for keyword in motion.keywords:
                if keyword in query:
                    score += 3
                elif any(word in keyword for word in query.split()):
                    score += 1

            # Description word matches
            query_words = set(query.split())
            desc_words = set(motion.description.lower().split())
            overlap = len(query_words & desc_words)
            score += overlap * 0.5

            if score > 0:
                scores.append((motion, score))

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        return [m for m, s in scores]

    def _calculate_confidence(self, query: str, motion: MotionEntry) -> float:
        """Calculate confidence score for a match."""
        confidence = 0.5  # Base confidence

        # Boost for exact keyword matches
        for keyword in motion.keywords:
            if keyword in query:
                confidence += 0.1

        # Boost for name matches
        if motion.name in query:
            confidence += 0.2

        # Cap at 1.0
        return min(confidence, 1.0)

    def _generate_explanation(
        self, query: str, motion: MotionEntry, confidence: float
    ) -> str:
        """Generate explanation for the match."""
        conf_level = "high" if confidence > 0.7 else "moderate" if confidence > 0.4 else "low"

        explanation = f"Based on your request '{query}', I've selected the "
        explanation += f"'{motion.display_name}' motion ({conf_level} confidence). "
        explanation += motion.description

        if motion.training_status == "trained":
            explanation += " This motion has been trained and is ready for playback."
        elif motion.training_status == "training":
            explanation += " This motion is currently being trained."
        elif motion.training_status == "ready":
            explanation += " This motion is processed and ready for training."
        else:
            explanation += " This motion is pending processing."

        return explanation

    def _llm_route(self, query: str) -> Optional[RoutingResult]:
        """Use LLM to route query to motion."""
        client = self._get_openai_client()
        if not client:
            return None

        try:
            # Build motion list for the prompt
            motion_list = "\n".join(
                f"- {m.name}: {m.display_name} - {m.description[:100]}"
                for m in self.catalog.list_motions()
            )

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are a motion selection assistant for a humanoid robot.
Given a user's request, select the most appropriate motion from the available options.

Available motions:
{motion_list}

Respond with ONLY the motion name (e.g., "bow_greeting") and nothing else.""",
                    },
                    {"role": "user", "content": query},
                ],
                max_tokens=50,
                temperature=0.3,
            )

            motion_name = response.choices[0].message.content.strip().lower()
            motion = self.catalog.get_motion(motion_name)

            if motion:
                return RoutingResult(
                    query=query,
                    matched_motion=motion,
                    confidence=0.8,
                    explanation=f"Based on your request, I've selected '{motion.display_name}'. "
                    + motion.description,
                    alternatives=[],
                )

        except Exception as e:
            print(f"LLM routing failed: {e}")

        return None

    def list_available_commands(self) -> str:
        """Get a list of example commands."""
        examples = [
            "show me a greeting",
            "make the robot bow",
            "do something celebratory",
            "show the dance",
            "wave hello",
            "what motions are available?",
        ]
        return "Try saying:\n" + "\n".join(f"  - {ex}" for ex in examples)


def route_prompt(query: str, use_llm: bool = False) -> RoutingResult:
    """Convenience function to route a prompt."""
    router = PromptRouter(use_llm=use_llm)
    return router.route(query)
