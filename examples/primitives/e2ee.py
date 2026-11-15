import logging
import os

from dotenv import load_dotenv

from livekit import rtc
from livekit.agents import AgentServer, JobContext, cli

logger = logging.getLogger("e2ee-example")
logger.setLevel(logging.INFO)

load_dotenv()

server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    e2ee_config = rtc.E2EEOptions(
        key_provider_options=rtc.KeyProviderOptions(
            shared_key=os.environ["LIVEKIT_E2EE_KEY"].encode(),
        ),
        encryption_type=rtc.EncryptionType.GCM,
    )

    await ctx.connect(encryption=e2ee_config)


if __name__ == "__main__":
    cli.run_app(server)
