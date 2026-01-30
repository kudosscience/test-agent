import json
import random
from uuid import uuid4
from a2a.server.tasks import TaskUpdater
from a2a.types import Message, TaskState, Part, TextPart
from a2a.utils import get_message_text, new_agent_text_message

from messenger import Messenger


# Assessment tasks for evaluating participant agents
ASSESSMENT_TASKS = [
    {
        "id": "math-001",
        "category": "math",
        "task": "What is 15 multiplied by 7?",
        "expected": "105",
        "keywords": ["105"],
        "points": 10,
    },
    {
        "id": "math-002",
        "category": "math",
        "task": "Calculate the sum of 234 and 567.",
        "expected": "801",
        "keywords": ["801"],
        "points": 10,
    },
    {
        "id": "reasoning-001",
        "category": "reasoning",
        "task": "If all roses are flowers and some flowers fade quickly, can we conclude that some roses fade quickly?",
        "expected": "No, we cannot conclude that.",
        "keywords": ["no", "cannot", "not necessarily", "invalid"],
        "points": 15,
    },
    {
        "id": "knowledge-001",
        "category": "knowledge",
        "task": "What is the capital of France?",
        "expected": "Paris",
        "keywords": ["paris"],
        "points": 10,
    },
    {
        "id": "knowledge-002",
        "category": "knowledge",
        "task": "What is the chemical symbol for water?",
        "expected": "H2O",
        "keywords": ["h2o"],
        "points": 10,
    },
    {
        "id": "coding-001",
        "category": "coding",
        "task": "Write a Python function that returns the factorial of a number n.",
        "expected": "def factorial(n): return 1 if n <= 1 else n * factorial(n-1)",
        "keywords": ["def", "factorial", "return", "*", "n"],
        "points": 20,
    },
]


class Agent:
    """Green Agent (Assessor) for AgentBeats platform.
    
    This agent follows the AgentBeats specification for a Green Agent:
    - Sets up task environments
    - Sends instructions to participant agents
    - Evaluates responses and calculates scores
    """
    
    def __init__(self):
        self.messenger = Messenger()
        self.active_assessments = {}  # context_id -> assessment state

    async def run(self, message: Message, updater: TaskUpdater) -> None:
        """Process incoming messages and manage assessments.

        Args:
            message: The incoming message from a participant or orchestrator
            updater: Report progress (update_status) and results (add_artifact)
        """
        input_text = get_message_text(message).strip()
        context_id = message.context_id

        await updater.update_status(
            TaskState.working, new_agent_text_message("🟢 Processing request...")
        )

        # Parse the command/request
        response = await self._handle_request(input_text, context_id)

        await updater.add_artifact(
            parts=[Part(root=TextPart(text=response))],
            name="Assessment Response",
        )

    async def _handle_request(self, input_text: str, context_id: str | None) -> str:
        """Handle different types of requests to the assessor."""
        lower_input = input_text.lower()

        # Command: Start a new assessment
        if lower_input.startswith("start assessment") or lower_input == "start":
            return self._start_assessment(context_id)

        # Command: Force start a new assessment (discard existing)
        if lower_input == "start new":
            if context_id and context_id in self.active_assessments:
                del self.active_assessments[context_id]
            return self._start_assessment(context_id)

        # Command: Get next task
        if lower_input in ["next", "next task", "get task"]:
            return self._get_next_task(context_id)

        # Command: Submit answer
        if lower_input.startswith("submit:") or lower_input.startswith("answer:"):
            answer = input_text.split(":", 1)[1].strip() if ":" in input_text else ""
            return self._evaluate_answer(context_id, answer)

        # Command: Get current score
        if lower_input in ["score", "get score", "my score", "results"]:
            return self._get_score(context_id)

        # Command: List available tasks
        if lower_input in ["list tasks", "tasks", "help"]:
            return self._get_help()

        # Command: End assessment
        if lower_input in ["end", "finish", "done", "end assessment"]:
            return self._end_assessment(context_id)

        # Default: Treat as an answer submission if in active assessment
        if context_id and context_id in self.active_assessments:
            state = self.active_assessments[context_id]
            if state.get("current_task"):
                return self._evaluate_answer(context_id, input_text)

        # Unknown command
        return self._get_help()

    def _start_assessment(self, context_id: str | None) -> str:
        """Initialize a new assessment session."""
        # Check if an assessment already exists for this context
        if context_id and context_id in self.active_assessments:
            state = self.active_assessments[context_id]
            return f"""⚠️ **Assessment Already in Progress**

You have an active assessment session.
**Progress:** {len(state["completed"])}/{len(state["tasks"])} tasks completed
**Score:** {state["score"]}/{state["max_score"]} points

Use `next` to continue, `end` to finish current assessment, or type `start new` to discard current progress and start fresh."""
        
        if not context_id:
            context_id = f"session-{uuid4().hex[:12]}"
        
        # Shuffle tasks for this session
        tasks = ASSESSMENT_TASKS.copy()
        random.shuffle(tasks)
        
        self.active_assessments[context_id] = {
            "tasks": tasks,
            "task_index": 0,
            "score": 0,
            "max_score": sum(t["points"] for t in tasks),
            "completed": [],
            "current_task": None,
        }
        
        return f"""🟢 **Green Agent Assessment Started**

Welcome to the AgentBeats assessment! I am a Green Agent (Assessor).

**Session ID:** {context_id}
**Total Tasks:** {len(tasks)}
**Maximum Score:** {sum(t["points"] for t in tasks)} points

**Commands:**
- `next` - Get the next task
- `submit: <your answer>` - Submit your answer
- `score` - View your current score
- `end` - End the assessment

Type `next` to receive your first task."""

    def _get_next_task(self, context_id: str | None) -> str:
        """Get the next task for the participant."""
        if not context_id or context_id not in self.active_assessments:
            return "⚠️ No active assessment. Type `start` to begin a new assessment."
        
        state = self.active_assessments[context_id]
        
        if state["task_index"] >= len(state["tasks"]):
            return self._end_assessment(context_id)
        
        task = state["tasks"][state["task_index"]]
        state["current_task"] = task
        
        return f"""🟢 **Task {state["task_index"] + 1} of {len(state["tasks"])}**

**Category:** {task["category"].title()}
**Points:** {task["points"]}

**Task:**
{task["task"]}

---
Submit your answer with `submit: <your answer>` or just type your answer directly."""

    def _evaluate_answer(self, context_id: str | None, answer: str) -> str:
        """Evaluate a submitted answer."""
        if not context_id or context_id not in self.active_assessments:
            return "⚠️ No active assessment. Type `start` to begin a new assessment."
        
        state = self.active_assessments[context_id]
        task = state.get("current_task")
        
        if not task:
            return "⚠️ No current task. Type `next` to get a task."
        
        # Evaluate the answer
        answer_lower = answer.lower()
        keywords_found = sum(1 for kw in task["keywords"] if kw.lower() in answer_lower)
        total_keywords = len(task["keywords"])
        
        # Calculate score based on keyword matches
        if keywords_found == total_keywords:
            earned_points = task["points"]
            result = "✅ **Correct!**"
        elif keywords_found > 0:
            earned_points = round(task["points"] * (keywords_found / total_keywords))
            result = f"🟡 **Partially Correct** ({keywords_found}/{total_keywords} criteria met)"
        else:
            earned_points = 0
            result = "❌ **Incorrect**"
        
        state["score"] += earned_points
        state["completed"].append({
            "task_id": task["id"],
            "answer": answer,
            "earned": earned_points,
            "max": task["points"],
        })
        state["current_task"] = None
        state["task_index"] += 1
        
        remaining = len(state["tasks"]) - state["task_index"]
        
        response = f"""🟢 **Evaluation Result**

{result}

**Points Earned:** {earned_points}/{task["points"]}
**Current Score:** {state["score"]}/{state["max_score"]}
**Tasks Remaining:** {remaining}

"""
        if remaining > 0:
            response += "Type `next` for the next task or `end` to finish."
        else:
            response += "🎉 Assessment complete! Type `score` to see your final results."
        
        return response

    def _get_score(self, context_id: str | None) -> str:
        """Get the current score for the assessment."""
        if not context_id or context_id not in self.active_assessments:
            return "⚠️ No active assessment. Type `start` to begin a new assessment."
        
        state = self.active_assessments[context_id]
        completed_count = len(state["completed"])
        total_count = len(state["tasks"])
        
        score_data = {
            "session_id": context_id,
            "score": state["score"],
            "max_score": state["max_score"],
            "percentage": round(100 * state["score"] / state["max_score"], 1) if state["max_score"] > 0 else 0,
            "tasks_completed": completed_count,
            "tasks_total": total_count,
        }
        
        breakdown = "\n".join([
            f"  - {c['task_id']}: {c['earned']}/{c['max']} points"
            for c in state["completed"]
        ]) or "  No tasks completed yet."
        
        return f"""🟢 **Assessment Score**

**Session:** {context_id}
**Score:** {score_data["score"]}/{score_data["max_score"]} ({score_data["percentage"]}%)
**Progress:** {completed_count}/{total_count} tasks completed

**Task Breakdown:**
{breakdown}

---
```json
{json.dumps(score_data, indent=2)}
```"""

    def _end_assessment(self, context_id: str | None) -> str:
        """End the assessment and provide final results."""
        if not context_id or context_id not in self.active_assessments:
            return "⚠️ No active assessment to end."
        
        state = self.active_assessments[context_id]
        final_score = self._get_score(context_id)
        
        # Clean up
        del self.active_assessments[context_id]
        
        return f"""🟢 **Assessment Completed**

{final_score}

Thank you for participating in the AgentBeats assessment!
Your results have been recorded.

Type `start` to begin a new assessment."""

    def _get_help(self) -> str:
        """Return help information about the assessor."""
        return """🟢 **Green Agent (Assessor) - AgentBeats**

I am a Green Agent, responsible for evaluating participant agents.

**Available Commands:**
- `start` - Start a new assessment session
- `next` - Get the next task
- `submit: <answer>` - Submit your answer to the current task
- `score` - View your current score
- `end` - End the assessment and see final results
- `help` - Show this help message

**Assessment Categories:**
- Math - Basic arithmetic and calculations
- Reasoning - Logical reasoning questions
- Knowledge - General knowledge questions
- Coding - Programming tasks

**How it works:**
1. Start an assessment with `start`
2. Request tasks with `next`
3. Submit answers with `submit: <your answer>`
4. View results with `score`
5. End with `end`

Type `start` to begin!"""
