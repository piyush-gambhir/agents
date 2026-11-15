import asyncio
import logging
from collections.abc import AsyncIterable

from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    cli,
    llm,
)
from livekit.agents.llm.chat_context import ChatContext, ChatMessage
from livekit.plugins import deepgram, groq, openai, silero

logger = logging.getLogger("pre-reseponse-agent")

load_dotenv()


class PreResponseAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions="You are a helpful assistant",
            llm=groq.LLM(model="llama-3.3-70b-versatile"),
        )
        self._fast_llm = groq.LLM(model="llama-3.1-8b-instant")
        self._fast_llm_prompt = llm.ChatMessage(
            role="system",
            content=[
                "Generate a short instant response to the user's message with 5 to 10 words.",
                "Do not answer the questions directly. Examples:, let me think about that, "
                "wait a moment, that's a good question, etc.",
            ],
        )

    async def on_user_turn_completed(self, turn_ctx: ChatContext, new_message: ChatMessage):

        fast_llm_ctx = turn_ctx.copy(
            exclude_instructions=True,
            exclude_function_call=True,
            exclude_handoff=True,
            exclude_config_update=True,
        ).truncate(max_items=3)
        fast_llm_ctx.items.insert(0, self._fast_llm_prompt)
        fast_llm_ctx.items.append(new_message)

        fast_llm_fut = asyncio.Future[str]()

        async def _fast_llm_reply() -> AsyncIterable[str]:
            filler_response: str = ""
            async for chunk in self._fast_llm.chat(chat_ctx=fast_llm_ctx).to_str_iterable():
                filler_response += chunk
                yield chunk
            fast_llm_fut.set_result(filler_response)

        self.session.say(_fast_llm_reply(), add_to_chat_ctx=False)

        filler_response = await fast_llm_fut
        logger.info(f"Fast response: {filler_response}")
        turn_ctx.add_message(role="assistant", content=filler_response, interrupted=False)


server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    session = AgentSession(
        stt=deepgram.STT(),
        tts=openai.TTS(),
        vad=silero.VAD.load(),
    )
    await session.start(PreResponseAgent(), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(server)
