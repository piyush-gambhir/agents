import logging
import random
from enum import Enum
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    ChatContext,
    FunctionTool,
    JobContext,
    ModelSettings,
    cli,
    function_tool,
    inference,
)
from livekit.plugins import silero

logger = logging.getLogger("grok-agent")
logger.setLevel(logging.INFO)

load_dotenv()


class MyAgent(Agent):
    def __init__(self, instructions: str, tools: list[FunctionTool]) -> None:
        super().__init__(instructions=instructions, tools=tools)

    async def llm_node(
        self, chat_ctx: ChatContext, tools: list[FunctionTool], model_settings: ModelSettings
    ):

        async def _get_weather(location: str) -> str:
            return f"The weather in {location} is sunny."

        tools.append(
            function_tool(
                _get_weather,
                name="get_weather",
                description="Get the weather in a specific location",
            )
        )

        return Agent.default.llm_node(self, chat_ctx, tools, model_settings)


async def _get_course_list_from_db() -> list[str]:
    """
    This function simulates a database call but actually returns a hardcoded list.
    In a real application, you would replace this with logic to retrieve data
    from a real database or external data source.
    """
    return [
        "Applied mathematics",
        "Data Science",
        "Machine Learning",
        "Deep Learning",
        "Voice Agents",
    ]


server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext):

    courses = await _get_course_list_from_db()

    CourseType = Enum("CourseType", {c.replace(" ", "_"): c for c in courses})

    class CourseInfo(BaseModel):
        course: CourseType  # type: ignore
        location: Literal["online", "in-person"]

    async def _get_course_info(info: CourseInfo) -> str:
        logger.info(f"get_course_info called: {info}")
        return f"Imagine a course about {info.course}."

    agent = MyAgent(
        instructions="You are a helpful assistant that can answer questions and help with tasks.",
        tools=[
            function_tool(
                _get_course_info,
                name="get_course_info",
                description="Get information about a course",
            )
        ],
    )

    async def _random_number() -> int:
        num = random.randint(0, 100)
        logger.info(f"random_number called: {num}")
        return num

    await agent.update_tools(
        agent.tools
        + [function_tool(_random_number, name="random_number", description="Get a random number")]
    )

    session = AgentSession(
        vad=silero.VAD.load(),
        stt=inference.STT("deepgram/nova-3"),
        llm=inference.LLM("openai/gpt-4.1-mini"),
        tts=inference.TTS("cartesia/sonic-3"),
    )
    await session.start(agent, room=ctx.room)


if __name__ == "__main__":
    cli.run_app(server)
