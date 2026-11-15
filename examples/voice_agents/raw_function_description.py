import logging

from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    RunContext,
    cli,
    function_tool,
)
from livekit.plugins import openai, silero  # noqa: F401










logger = logging.getLogger("raw-function-description")

load_dotenv()


class RawFunctionAgent(Agent):
    def __init__(self):
        super().__init__(instructions="You are a helpful assistant")

    @function_tool(
        raw_schema={
            "name": "open_gate",
            "description": "Opens a specified gate from a predefined set of access points.",
            "parameters": {
                "type": "object",
                "properties": {
                    "gate_id": {
                        "type": "string",
                        "description": (
                            "Identifier of the gate to open. Must be one of the "
                            "system's predefined access points."
                        ),
                        "enum": [
                            "main_entrance",
                            "north_parking",
                            "loading_dock",
                            "side_gate",
                            "service_entry",
                        ],
                    }
                },
                "required": ["gate_id"],
            },
        }
    )
    async def open_gate(self, raw_arguments: dict[str, object], ctx: RunContext):
        gate_id = raw_arguments["gate_id"]
        logger.info(f"Opening gate: {gate_id}")
        return f"Gate {gate_id} opened successfully"


server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    session = AgentSession(




        llm=openai.realtime.RealtimeModel()
    )
    await session.start(RawFunctionAgent(), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(server)
