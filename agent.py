# agent.py

import logging
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.llm import function_tool
from livekit.agents.voice import Agent, AgentSession, RunContext
from livekit.plugins import cartesia, deepgram, openai, silero

from dummy_data import PRODUCTS, ORDERS, RETURNS

from utils import load_prompt

logger = logging.getLogger("ecommerce-shopping-triage")
logger.setLevel(logging.INFO)

load_dotenv()


@dataclass
class UserData:
    """Stores data and agents to be shared across the session"""

    personas: dict[str, Agent] = field(default_factory=dict)
    prev_agent: Optional[Agent] = None
    ctx: Optional[JobContext] = None

    def summarize(self) -> str:
        return "User data: E-commerce customer journey triage system"


RunContext_T = RunContext[UserData]


class BaseAgent(Agent):
    async def on_enter(self) -> None:
        agent_name = self.__class__.__name__
        logger.info(f"Entering {agent_name}")

        userdata: UserData = self.session.userdata
        if userdata.ctx and userdata.ctx.room:
            await userdata.ctx.room.local_participant.set_attributes(
                {"agent": agent_name}
            )

        chat_ctx = self.chat_ctx.copy()

        if userdata.prev_agent:
            items_copy = self._truncate_chat_ctx(
                userdata.prev_agent.chat_ctx.items, keep_function_call=True
            )
            existing_ids = {item.id for item in chat_ctx.items}
            items_copy = [item for item in items_copy if item.id not in existing_ids]
            chat_ctx.items.extend(items_copy)

        chat_ctx.add_message(
            role="system", content=f"You are the {agent_name}. {userdata.summarize()}"
        )
        await self.update_chat_ctx(chat_ctx)
        self.session.generate_reply()

    def _truncate_chat_ctx(
        self,
        items: list,
        keep_last_n_messages: int = 6,
        keep_system_message: bool = False,
        keep_function_call: bool = False,
    ) -> list:
        """Truncate the chat context to keep the last n messages."""

        def _valid_item(item) -> bool:
            if (
                not keep_system_message
                and item.type == "message"
                and item.role == "system"
            ):
                return False
            if not keep_function_call and item.type in [
                "function_call",
                "function_call_output",
            ]:
                return False
            return True

        new_items = []
        for item in reversed(items):
            if _valid_item(item):
                new_items.append(item)
            if len(new_items) >= keep_last_n_messages:
                break
        new_items = new_items[::-1]

        while new_items and new_items[0].type in [
            "function_call",
            "function_call_output",
        ]:
            new_items.pop(0)

        return new_items

    async def _transfer_to_agent(self, name: str, context: RunContext_T) -> Agent:
        """Transfer to another agent while preserving context"""
        userdata = context.userdata
        current_agent = context.session.current_agent
        next_agent = userdata.personas[name]
        userdata.prev_agent = current_agent

        return next_agent


class TriageAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            instructions=load_prompt("triage_prompt.yaml"),
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=cartesia.TTS(),
            vad=silero.VAD.load(),
        )

    @function_tool
    async def transfer_to_pre_purchase(self, context: RunContext_T) -> Agent:
        await self.session.say(
            "I'll transfer you to our Shopping Assistant who can help with product questions."
        )
        return await self._transfer_to_agent("pre_purchase", context)

    @function_tool
    async def transfer_to_post_purchase(self, context: RunContext_T) -> Agent:
        await self.session.say(
            "I'll transfer you to our Order Support team who can assist with your order."
        )
        return await self._transfer_to_agent("post_purchase", context)

    @function_tool
    async def transfer_to_after_sales(self, context: RunContext_T) -> Agent:
        await self.session.say(
            "I'll transfer you to our After Sales team who can assist with returns and refunds."
        )
        return await self._transfer_to_agent("after_sales", context)


class PrePurchaseAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            instructions=load_prompt("pre_purchase_prompt.yaml"),
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=cartesia.TTS(),
            vad=silero.VAD.load(),
        )

    @function_tool
    async def transfer_to_triage(self, context: RunContext_T) -> Agent:
        await self.session.say(
            "I'll transfer you back to our assistant to better route your question."
        )
        return await self._transfer_to_agent("triage", context)

    @function_tool
    async def list_products(self, context: RunContext_T) -> str:
        """Show the list of products available"""
        spoken_list = [
            f"{p['name']}, priced at {int(p['price'])} dollars"
            if p["price"].is_integer()
            else f"{p['name']}, priced at {p['price']} dollars"
            for p in PRODUCTS
        ]
        product_lines = "; ".join(spoken_list)
        return f"We currently have the following Samsung products available: {product_lines}."


class PostPurchaseAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            instructions=load_prompt("post_purchase_prompt.yaml"),
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=cartesia.TTS(),
            vad=silero.VAD.load(),
        )

    @function_tool
    async def transfer_to_triage(self, context: RunContext_T) -> Agent:
        await self.session.say(
            "I'll transfer you back to our assistant to better route your question."
        )
        return await self._transfer_to_agent("triage", context)

    @function_tool
    async def check_order_status(self, context: RunContext_T, order_id: str) -> str:
        """Check the shipping status of an order"""
        for order in ORDERS:
            if order["order_id"] == order_id:
                return f"Your order {order_id} is currently '{order['status']}'."
        return f"Sorry, we couldn’t find an order with ID {order_id}."


class AfterSalesAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            instructions=load_prompt("after_sales_prompt.yaml"),
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=cartesia.TTS(),
            vad=silero.VAD.load(),
        )

    @function_tool
    async def transfer_to_triage(self, context: RunContext_T) -> Agent:
        await self.session.say(
            "I'll transfer you back to our assistant to better route your question."
        )
        return await self._transfer_to_agent("triage", context)

    @function_tool
    async def request_return(self, context: RunContext_T, order_id: str) -> str:
        """Submit a return request for an order"""
        for order in ORDERS:
            if order["order_id"] == order_id:
                RETURNS.append({"order_id": order_id, "status": "Return Requested"})
                return f"We’ve submitted a return request for order {order_id}."
        return f"Sorry, we couldn’t find an order with ID {order_id}."


async def entrypoint(ctx: JobContext):
    await ctx.connect()

    userdata = UserData(ctx=ctx)
    triage_agent = TriageAgent()
    pre_purchase_agent = PrePurchaseAgent()
    post_purchase_agent = PostPurchaseAgent()
    after_sales_agent = AfterSalesAgent()

    userdata.personas.update(
        {
            "triage": triage_agent,
            "pre_purchase": pre_purchase_agent,
            "post_purchase": post_purchase_agent,
            "after_sales": after_sales_agent,
        }
    )
    session = AgentSession[UserData](userdata=userdata)

    await session.start(
        agent=triage_agent,
        room=ctx.room,
    )

    await session.say("Hi!")


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(entrypoint_fnc=entrypoint, agent_name="ecommerce-cs-agent")
    )
