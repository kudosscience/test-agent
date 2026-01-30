import argparse
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)

from executor import Executor


def main():
    parser = argparse.ArgumentParser(description="Run the A2A agent.")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind the server")
    parser.add_argument("--port", type=int, default=9009, help="Port to bind the server")
    parser.add_argument("--card-url", type=str, help="URL to advertise in the agent card")
    args = parser.parse_args()

    # Green Agent (Assessor) Card Configuration for AgentBeats
    # See: https://agentbeats.dev/
    # Green Agent = Assessment/Evaluator that sets tasks, scores results
    
    skill = AgentSkill(
        id="assessment",
        name="Agent Assessment",
        description="Evaluates participant agents by setting tasks, scoring results, and providing structured feedback. Supports math, reasoning, knowledge, and coding assessments.",
        tags=["assessment", "evaluation", "benchmark", "agentbeats", "green-agent", "scoring"],
        examples=[
            "start",
            "next",
            "submit: 105",
            "score",
            "end",
            "help",
        ]
    )

    agent_card = AgentCard(
        name="Green Agent (Assessor)",
        description="An AgentBeats Green Agent that evaluates participant agents. Sets tasks, scores results, and provides structured assessment feedback. Supports math, reasoning, knowledge, and coding evaluations.",
        url=args.card_url or f"http://{args.host}:{args.port}/",
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill]
    )

    request_handler = DefaultRequestHandler(
        agent_executor=Executor(),
        task_store=InMemoryTaskStore(),
    )
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )
    uvicorn.run(server.build(), host=args.host, port=args.port)


if __name__ == '__main__':
    main()
