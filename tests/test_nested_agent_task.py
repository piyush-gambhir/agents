from __future__ import annotations

import asyncio

import pytest

from livekit.agents import Agent, AgentSession, AgentTask, RunContext, function_tool
from livekit.agents.llm import FunctionToolCall

from .fake_llm import FakeLLM, FakeLLMResponse

pytestmark = pytest.mark.unit


class InnerTask(AgentTask):
    """A task that needs a second user turn to complete (user must trigger 'finish')."""

    def __init__(self) -> None:
        super().__init__(instructions="inner task")

    async def on_enter(self) -> None:
        self.session.generate_reply(instructions="inner_greeting")

    @function_tool
    async def finish(self, ctx: RunContext) -> str:
        """Called to complete the inner task."""
        self.complete(None)
        return "done"


class OuterTask(AgentTask):
    """A task whose on_enter triggers a tool call that awaits InnerTask."""

    def __init__(self) -> None:
        super().__init__(instructions="outer task")

    async def on_enter(self) -> None:
        await self.session.generate_reply(instructions="outer_greeting")

    @function_tool
    async def start_inner(self, ctx: RunContext) -> str:
        """Transitions into InnerTask."""
        await InnerTask()
        self.complete(None)
        return "inner completed"


class RootAgent(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="root agent")

    @function_tool
    async def start_outer(self, ctx: RunContext) -> str:
        """Transitions into OuterTask."""
        await OuterTask()
        return "outer completed"


@pytest.mark.asyncio
async def test_nested_agent_task_no_deadlock():
    """session.run() must return when an AgentTask hands off to a nested task
    that collects additional user input before completing."""
    llm = _build_fake_llm()
    async with AgentSession(llm=llm) as sess:
        await sess.start(RootAgent())

        first_result = await asyncio.wait_for(sess.run(user_input="go"), timeout=5.0)
        assert first_result is not None

        second_result = await asyncio.wait_for(sess.run(user_input="done"), timeout=5.0)
        assert second_result is not None


def _build_fake_llm() -> FakeLLM:
    return FakeLLM(
        fake_responses=[
            FakeLLMResponse(
                input="go",
                content="",
                ttft=0,
                duration=0,
                tool_calls=[FunctionToolCall(name="start_outer", arguments="{}", call_id="call_1")],
            ),
            FakeLLMResponse(
                input="outer_greeting",
                content="",
                ttft=0,
                duration=0,
                tool_calls=[FunctionToolCall(name="start_inner", arguments="{}", call_id="call_2")],
            ),
            FakeLLMResponse(
                input="inner_greeting",
                content="hello from inner",
                ttft=0,
                duration=0,
            ),
            FakeLLMResponse(
                input="done",
                content="",
                ttft=0,
                duration=0,
                tool_calls=[FunctionToolCall(name="finish", arguments="{}", call_id="call_3")],
            ),
            FakeLLMResponse(
                input="inner completed",
                content="",
                ttft=0,
                duration=0,
            ),
            FakeLLMResponse(
                input="outer completed",
                content="all done",
                ttft=0,
                duration=0,
            ),
        ]
    )
