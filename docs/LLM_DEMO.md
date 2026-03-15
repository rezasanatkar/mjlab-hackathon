# FBX2Robot LLM Demo Layer

The LLM demo layer provides an interactive judge-facing interface for demonstrating
the FBX2Robot pipeline. It supports natural language queries, motion selection,
and playback integration.

## Quick Start

### Interactive CLI Demo

```bash
# Basic demo
python scripts/run_demo.py

# With LLM enhancement
python scripts/run_demo.py --use-llm

# Process a single query
python scripts/run_demo.py --query "show me a greeting"

# Print demo script for judges
python scripts/run_demo.py --script
```

### Streamlit Web Demo

```bash
# Install streamlit (if not already installed)
uv pip install streamlit

# Run web demo
uv run streamlit run scripts/run_streamlit_demo.py
```

## Architecture

The LLM demo layer consists of these components:

### Motion Catalog (`motion_catalog.py`)

Manages the catalog of available motions and their metadata.

```python
from fbx2robot.llm_demo import get_catalog

catalog = get_catalog()
motions = catalog.list_motions()
trained = catalog.list_trained_motions()
results = catalog.search_by_keyword("greeting")
```

### Prompt Router (`prompt_router.py`)

Routes natural language queries to appropriate motions.

```python
from fbx2robot.llm_demo import route_prompt

result = route_prompt("show me a bow greeting")
print(result.matched_motion)  # MotionEntry for bow_greeting
print(result.confidence)       # 0.7
print(result.explanation)      # Description of the match
```

### Demo Narrator (`narrator.py`)

Generates explanations and narration for the demo.

```python
from fbx2robot.llm_demo import get_narrator

narrator = get_narrator(use_llm=False)
print(narrator.introduce_project())
print(narrator.summarize_results())
```

### Conversation Manager (`conversation.py`)

Handles multi-turn conversations with context.

```python
from fbx2robot.llm_demo import ConversationManager

conv = ConversationManager(use_llm=True)
response = conv.process_message("show me a dance")
response = conv.process_message("play it")
```

### Demo Runner (`demo_runner.py`)

Main orchestration for the demo.

```python
from fbx2robot.llm_demo import DemoRunner

runner = DemoRunner(use_llm=False)
runner.run_interactive()  # Interactive CLI session
```

## Demo Script

The included demo script provides a structured walkthrough for judges:

1. **Introduction**: Overview of FBX2Robot
2. **Pipeline Flow**: How animations become robot motions
3. **Motion Selection**: Interactive query demonstration
4. **Playback**: Live motion execution
5. **Q&A**: Answer judge questions

Run `python scripts/run_demo.py --script` to see the full script.

## LLM Enhancement

When `use_llm=True`, the demo uses OpenAI's GPT-4o-mini for:

- Enhanced natural language understanding
- Better motion matching
- Contextual Q&A responses

Set your API key:
```bash
export OPENAI_API_KEY=your-key-here
```

Or pass it in code:
```python
from fbx2robot.config import Config
config = Config(openai_api_key="your-key")
```

## Web Demo Features

The Streamlit web demo includes:

- **Interactive Chat**: Natural language motion queries
- **Motion Catalog**: Browse all available motions
- **Training Status**: View progress and metrics
- **How It Works**: Technical explanation

## Example Queries

The system understands queries like:

- "Show me a greeting"
- "Make the robot bow"
- "Do something celebratory"
- "Play the dance"
- "What motions are available?"
- "How does this work?"

## Integration with Training

After training completes, update the catalog:

```python
from fbx2robot.llm_demo import get_catalog

catalog = get_catalog()
catalog.update_motion(
    "bow_greeting",
    wandb_run_path="asggm03-startup/fbx2robot-hackathon/runs/abc123",
    training_status="trained",
)
catalog.save_catalog(Path("data/motion_catalog.json"))
```

## Troubleshooting

### Streamlit not found
```bash
uv pip install streamlit
```

### OpenAI errors
- Check API key is set
- Verify internet connection
- Check OpenAI account has credits

### Motion not playing
- Ensure motion is trained (status: "trained")
- Check W&B run path is correct
- Verify mjlab environment is active
