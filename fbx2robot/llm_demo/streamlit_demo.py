"""Streamlit-based web demo for FBX2Robot.

This provides a web-based interface for judges to interact with the system.
"""

import os
import subprocess
from pathlib import Path

# Check if streamlit is available
try:
    import streamlit as st

    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None


def check_streamlit():
    """Check if streamlit is available."""
    if not STREAMLIT_AVAILABLE:
        print("Streamlit not installed. Install with: uv pip install streamlit")
        return False
    return True


def run_demo():
    """Run the Streamlit demo."""
    if not check_streamlit():
        return

    st.set_page_config(
        page_title="FBX2Robot Demo",
        page_icon="🤖",
        layout="wide",
    )

    # Header
    st.title("🤖 FBX2Robot")
    st.subheader("Transform Animations into Robot Motion")

    # Sidebar
    with st.sidebar:
        st.header("About")
        st.markdown(
            """
        **FBX2Robot** transforms standard animation files 
        into trained robot motion policies.
        
        **Pipeline:**
        1. FBX Animation → Blender
        2. Motion Retargeting → G1 Joints
        3. Training Data → LAFAN CSV
        4. Policy Training → ONNX Model
        """
        )

        st.header("Settings")
        use_llm = st.checkbox("Use LLM Enhancement", value=False)
        if use_llm:
            api_key = st.text_input("OpenAI API Key", type="password")
            if api_key:
                os.environ["OPENAI_API_KEY"] = api_key

    # Import after streamlit is configured
    from fbx2robot.llm_demo.motion_catalog import get_catalog
    from fbx2robot.llm_demo.prompt_router import PromptRouter
    from fbx2robot.llm_demo.narrator import get_narrator

    catalog = get_catalog()
    router = PromptRouter(catalog=catalog, use_llm=use_llm if "use_llm" in dir() else False)
    narrator = get_narrator(use_llm=use_llm if "use_llm" in dir() else False)

    # Main content
    tab1, tab2, tab3, tab4 = st.tabs(
        ["💬 Interactive Demo", "📚 Motion Catalog", "📊 Training Status", "🎓 How It Works"]
    )

    with tab1:
        st.header("Interactive Demo")
        st.markdown("Tell the robot what motion you'd like to see!")

        # Chat interface
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat history
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Input
        if prompt := st.chat_input("What would you like to see?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Route the prompt
            result = router.route(prompt)

            response = result.explanation
            if result.matched_motion and result.matched_motion.training_status == "trained":
                response += "\n\n✅ This motion is trained and ready to play!"

            st.session_state.messages.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.markdown(response)

    with tab2:
        st.header("Motion Catalog")

        motions = catalog.list_motions()
        cols = st.columns(2)

        for i, motion in enumerate(motions):
            with cols[i % 2]:
                status_color = {
                    "trained": "🟢",
                    "training": "🟡",
                    "ready": "🔵",
                    "pending": "⚪",
                }.get(motion.training_status, "⚪")

                with st.expander(f"{status_color} {motion.display_name}"):
                    st.markdown(f"**Description:** {motion.description}")
                    st.markdown(f"**Status:** {motion.training_status}")
                    st.markdown(f"**Keywords:** {', '.join(motion.keywords[:5])}")

                    if motion.duration_seconds > 0:
                        st.markdown(f"**Duration:** {motion.duration_seconds:.1f}s")

                    if motion.wandb_run_path:
                        st.code(f"wandb: {motion.wandb_run_path}")

    with tab3:
        st.header("Training Status")

        summary = narrator.summarize_results()
        st.text(summary)

        st.subheader("Training Progress")

        trained = catalog.list_trained_motions()
        available = catalog.list_available_motions()
        total = len(catalog.list_motions())

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Motions", total)
        with col2:
            st.metric("Processed", len(available))
        with col3:
            st.metric("Trained", len(trained))

        st.progress(len(trained) / max(total, 1))

    with tab4:
        st.header("How FBX2Robot Works")

        st.markdown(narrator.introduce_project())

        st.subheader("Pipeline Flow")

        st.markdown(
            """
        ```
        FBX File → Blender (headless) → Canonical Motion → Retargeting → CSV → NPZ → Training → ONNX
        ```
        """
        )

        st.subheader("Technical Details")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                """
            **Input:**
            - Mixamo FBX animations
            - Any humanoid skeleton

            **Processing:**
            - Blender 5.0 headless extraction
            - Scipy quaternion math
            - 29-DOF joint mapping
            """
            )

        with col2:
            st.markdown(
                """
            **Training:**
            - 4096 parallel environments
            - GPU-accelerated physics
            - ~15 min per motion (RTX 4090)

            **Output:**
            - ONNX policy model
            - W&B experiment tracking
            """
            )


def main():
    """Entry point for streamlit app."""
    if check_streamlit():
        run_demo()


if __name__ == "__main__":
    main()
