import logging
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
)
from livekit.plugins import langchain, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("basic-agent")

load_dotenv()










server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]



def create_graph() -> StateGraph:
    openai_llm = init_chat_model(
        model="openai:gpt-4.1-mini",
    )

    def chatbot_node(state: State):
        return {"messages": [openai_llm.invoke(state["messages"])]}

    builder = StateGraph(State)
    builder.add_node("chatbot", chatbot_node)
    builder.add_edge(START, "chatbot")
    return builder.compile()


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    graph = create_graph()

    agent = Agent(
        instructions="",
        llm=langchain.LLMAdapter(graph),
    )

    session = AgentSession(
        vad=ctx.proc.userdata["vad"],

        stt=inference.STT("deepgram/nova-3", language="multi"),
        tts=inference.TTS("cartesia/sonic-3"),

        turn_detection=MultilingualModel(),
    )

    await session.start(
        agent=agent,
        room=ctx.room,
    )
    await session.generate_reply(instructions="ask the user how they are doing?")


if __name__ == "__main__":
    cli.run_app(server)
