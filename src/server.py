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

    # Green Agent Card Configuration
    # See: https://a2a-protocol.org/latest/tutorials/python/3-agent-skills-and-card/
    
    skill = AgentSkill(
        id="green-advice",
        name="Green Advice",
        description="Provides eco-friendly tips and sustainability advice to help reduce environmental impact",
        tags=["environment", "sustainability", "eco-friendly", "green", "tips", "advice"],
        examples=[
            "Give me a green tip",
            "How can I save water?",
            "What can I do to reduce plastic waste?",
            "Tips for saving energy at home",
            "How can I be more eco-friendly?",
        ]
    )

    agent_card = AgentCard(
        name="Green Agent",
        description="An eco-friendly assistant that provides sustainability tips and environmental advice to help you live a greener life. Ask about water conservation, energy saving, recycling, and more!",
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
