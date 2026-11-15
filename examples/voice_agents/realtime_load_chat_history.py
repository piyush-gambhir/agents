import logging

from dotenv import load_dotenv

from livekit.agents import Agent, AgentServer, AgentSession, JobContext, cli, llm
from livekit.plugins import openai

logger = logging.getLogger("realtime-load-chat-history")

load_dotenv()

server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    chat_history = [
        {
            "role": "assistant",
            "content": "Hello, I am a travel planner. How can I help you?",
        },
        {
            "role": "user",
            "content": "I want to go to Paris this summer.",
        },
        {
            "role": "assistant",
            "content": "Paris is a beautiful city. How many days will you be staying?",
        },
        {
            "role": "user",
            "content": "I'll have four days. What are the main attractions I should see?",
        },
    ]

    chat_ctx = llm.ChatContext.empty()
    for item in chat_history:
        chat_ctx.add_message(role=item["role"], content=item["content"])

    session = AgentSession()
    agent = Agent(
        instructions="You are a helpful travel planner.",
        llm=openai.realtime.RealtimeModel(voice="alloy", model="gpt-4o-mini-realtime-preview"),
        tts=openai.TTS(voice="alloy"),
        chat_ctx=chat_ctx,
    )

    await session.start(agent=agent, room=ctx.room)

    logger.info("Generating reply...")
    session.interrupt()
    session.generate_reply()


if __name__ == "__main__":
    cli.run_app(server)
