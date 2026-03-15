"""Conversation manager for the LLM demo.

Manages multi-turn conversations and context for the demo.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

from fbx2robot.llm_demo.motion_catalog import MotionEntry, get_catalog
from fbx2robot.llm_demo.prompt_router import PromptRouter, RoutingResult


@dataclass
class Message:
    """A single message in the conversation."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    motion_reference: Optional[MotionEntry] = None


@dataclass
class ConversationState:
    """State of the current conversation."""

    messages: List[Message] = field(default_factory=list)
    current_motion: Optional[MotionEntry] = None
    pending_action: Optional[str] = None
    demo_mode: str = "interactive"  # "interactive", "guided", "showcase"


class ConversationManager:
    """Manages multi-turn conversations for the demo."""

    def __init__(self, use_llm: bool = False):
        """Initialize conversation manager.

        Args:
            use_llm: Whether to use LLM for enhanced responses
        """
        self.catalog = get_catalog()
        self.router = PromptRouter(catalog=self.catalog, use_llm=use_llm)
        self.state = ConversationState()
        self.use_llm = use_llm
        self._openai_client = None

    def _get_openai_client(self):
        """Lazy-load OpenAI client."""
        if self._openai_client is None and self.use_llm:
            try:
                from openai import OpenAI

                api_key = os.environ.get("OPENAI_API_KEY")
                if api_key:
                    self._openai_client = OpenAI(api_key=api_key)
            except ImportError:
                pass
        return self._openai_client

    def process_message(self, user_input: str) -> str:
        """Process a user message and return response.

        Args:
            user_input: User's input message

        Returns:
            Assistant's response
        """
        user_message = Message(role="user", content=user_input)
        self.state.messages.append(user_message)

        response = self._generate_response(user_input)

        assistant_message = Message(
            role="assistant",
            content=response,
            motion_reference=self.state.current_motion,
        )
        self.state.messages.append(assistant_message)

        return response

    def _generate_response(self, user_input: str) -> str:
        """Generate response for user input."""
        input_lower = user_input.lower().strip()

        # Check for special commands
        if self._is_help_request(input_lower):
            return self._get_help_text()

        if self._is_list_request(input_lower):
            return self._get_motion_list()

        if self._is_confirmation(input_lower):
            return self._handle_confirmation()

        if self._is_negation(input_lower):
            return self._handle_negation()

        # Try to route to a motion
        result = self.router.route(user_input)

        if result.matched_motion:
            self.state.current_motion = result.matched_motion
            return self._format_motion_response(result)

        # If using LLM, try to generate a contextual response
        if self.use_llm:
            llm_response = self._get_llm_response(user_input)
            if llm_response:
                return llm_response

        # Fallback
        return self._get_fallback_response(user_input)

    def _is_help_request(self, text: str) -> bool:
        """Check if user is asking for help."""
        help_words = ["help", "what can you do", "commands", "options", "how to"]
        return any(w in text for w in help_words)

    def _is_list_request(self, text: str) -> bool:
        """Check if user wants to list motions."""
        list_words = ["list", "show all", "available", "what motions"]
        return any(w in text for w in list_words)

    def _is_confirmation(self, text: str) -> bool:
        """Check if user is confirming."""
        confirm_words = ["yes", "yeah", "yep", "sure", "ok", "okay", "play", "do it", "go ahead"]
        return any(text == w or text.startswith(w + " ") for w in confirm_words)

    def _is_negation(self, text: str) -> bool:
        """Check if user is declining."""
        negate_words = ["no", "nope", "cancel", "nevermind", "never mind", "don't"]
        return any(text == w or text.startswith(w + " ") for w in negate_words)

    def _get_help_text(self) -> str:
        """Get help text."""
        return """
I can help you explore and play robot motion animations!

**What you can say:**
- "Show me a greeting" - Find motions by description
- "Play the bow" - Play a specific motion
- "List motions" - See all available motions
- "What can you do?" - Get help (you're here!)

**Available motions:**
""" + "\n".join(f"- {m.display_name}" for m in self.catalog.list_motions())

    def _get_motion_list(self) -> str:
        """Get list of motions."""
        lines = ["**Available Motions:**\n"]
        for motion in self.catalog.list_motions():
            status = {
                "trained": "✅",
                "training": "🔄",
                "ready": "📦",
                "pending": "⏳",
            }.get(motion.training_status, "❓")
            lines.append(f"{status} **{motion.display_name}** - {motion.description[:50]}...")
        return "\n".join(lines)

    def _handle_confirmation(self) -> str:
        """Handle user confirmation."""
        if self.state.current_motion:
            if self.state.current_motion.training_status == "trained":
                return f"Playing '{self.state.current_motion.display_name}'... (use the play command)"
            else:
                return f"'{self.state.current_motion.display_name}' is not trained yet (status: {self.state.current_motion.training_status})"
        return "What would you like me to do?"

    def _handle_negation(self) -> str:
        """Handle user declining."""
        self.state.current_motion = None
        self.state.pending_action = None
        return "No problem! What else would you like to see?"

    def _format_motion_response(self, result: RoutingResult) -> str:
        """Format response for a motion match."""
        motion = result.matched_motion
        response = f"**{motion.display_name}**\n\n"
        response += f"{motion.description}\n\n"

        if motion.training_status == "trained":
            response += "✅ This motion is trained and ready! Say 'play' to watch it.\n"
        elif motion.training_status == "training":
            response += "🔄 This motion is currently being trained...\n"
        elif motion.training_status == "ready":
            response += "📦 This motion is processed but needs training.\n"
        else:
            response += "⏳ This motion is pending processing.\n"

        if result.alternatives:
            response += "\n**Similar motions:**\n"
            for alt in result.alternatives[:2]:
                response += f"- {alt.display_name}\n"

        return response

    def _get_fallback_response(self, user_input: str) -> str:
        """Get fallback response when nothing matches."""
        return f"""
I'm not sure what motion you're looking for with "{user_input}".

Try describing what you want to see, like:
- "Show me a greeting"
- "Make the robot dance"
- "Do something celebratory"

Or say "list" to see all available motions.
"""

    def _get_llm_response(self, user_input: str) -> Optional[str]:
        """Get LLM-generated response."""
        client = self._get_openai_client()
        if not client:
            return None

        try:
            # Build context from conversation history
            messages = [
                {
                    "role": "system",
                    "content": f"""You are an assistant for the FBX2Robot demo. 
You help users explore robot motions from animations.

Available motions: {', '.join(m.display_name for m in self.catalog.list_motions())}

Be helpful, concise, and guide users to try motions.""",
                }
            ]

            for msg in self.state.messages[-6:]:  # Last 6 messages for context
                messages.append({"role": msg.role, "content": msg.content})

            messages.append({"role": "user", "content": user_input})

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=200,
                temperature=0.7,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"LLM response failed: {e}")
            return None

    def get_conversation_summary(self) -> str:
        """Get summary of conversation so far."""
        if not self.state.messages:
            return "No conversation yet."

        summary = f"Conversation ({len(self.state.messages)} messages):\n"
        for msg in self.state.messages[-5:]:
            role_icon = "👤" if msg.role == "user" else "🤖"
            summary += f"{role_icon} {msg.content[:50]}...\n"

        if self.state.current_motion:
            summary += f"\nCurrent focus: {self.state.current_motion.display_name}"

        return summary

    def reset(self):
        """Reset conversation state."""
        self.state = ConversationState()
