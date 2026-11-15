from pathlib import Path

from dotenv import load_dotenv
from llama_index.core import (
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.core.schema import MetadataMode

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    AutoSubscribe,
    JobContext,
    cli,
    llm,
)
from livekit.agents.voice.agent import ModelSettings
from livekit.plugins import deepgram, openai, silero

load_dotenv()


THIS_DIR = Path(__file__).parent
PERSIST_DIR = THIS_DIR / "retrieval-engine-storage"
if not PERSIST_DIR.exists():

    documents = SimpleDirectoryReader(THIS_DIR / "data").load_data()
    index = VectorStoreIndex.from_documents(documents)

    index.storage_context.persist(persist_dir=PERSIST_DIR)
else:

    storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
    index = load_index_from_storage(storage_context)


class RetrievalAgent(Agent):
    def __init__(self, index: VectorStoreIndex):
        super().__init__(
            instructions=(
                "You are a voice assistant created by LiveKit. Your interface "
                "with users will be voice. You should use short and concise "
                "responses, and avoiding usage of unpronouncable punctuation."
            ),
            vad=silero.VAD.load(),
            stt=deepgram.STT(),
            llm=openai.LLM(),
            tts=openai.TTS(),
        )
        self.index = index

    async def llm_node(
        self,
        chat_ctx: llm.ChatContext,
        tools: list[llm.FunctionTool],
        model_settings: ModelSettings,
    ):
        user_msg = chat_ctx.items[-1]
        assert isinstance(user_msg, llm.ChatMessage) and user_msg.role == "user"
        user_query = user_msg.text_content
        assert user_query is not None

        retriever = self.index.as_retriever()
        nodes = await retriever.aretrieve(user_query)

        instructions = "Context that might help answer the user's question:"
        for node in nodes:
            node_content = node.get_content(metadata_mode=MetadataMode.LLM)
            instructions += f"\n\n{node_content}"



        system_msg = chat_ctx.items[0]
        if isinstance(system_msg, llm.ChatMessage) and system_msg.role == "system":

            system_msg.content.append(instructions)
        else:
            chat_ctx.items.insert(0, llm.ChatMessage(role="system", content=[instructions]))
        preview = instructions[:100].replace("\n", "\\n")
        print(f"update instructions: {preview}...")




        return Agent.default.llm_node(self, chat_ctx, tools, model_settings)


server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    agent = RetrievalAgent(index)
    session = AgentSession()
    await session.start(agent=agent, room=ctx.room)

    await session.say("Hey, how can I help you today?", allow_interruptions=False)


if __name__ == "__main__":
    cli.run_app(server)
