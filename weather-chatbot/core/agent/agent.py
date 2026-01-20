from __future__ import annotations

import asyncio
from typing import Annotated, List, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from core.agent.tools import WEATHER_TOOLS
from core.config import LLM_API_KEY, LLM_MODEL, LLM_TEMPERATURE, OLLAMA_BASE_URL

SYSTEM_PROMPT = (
    "You are a weather assistant. You only answer weather-related questions about "
    "current conditions or forecasts. If asked anything else, reply exactly: "
    "I can only answer weather related matters. "
    "Always use the tools to get live data. Use Celsius, wind in kph, humidity percent, "
    "and include air quality metrics from the tool results. If the user does not "
    "specify the number of days for a forecast, default to 3."
    "Always respond in a friendly and concise manner, in the language of the user."
)


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]


class WeatherAgent:
    def __init__(self, graph) -> None:
        self._graph = graph

    def run_stream(self, user_input: str, message_history: List[BaseMessage]):
        return _AgentRunStream(self, user_input, message_history)

    async def _run(
        self, user_input: str, message_history: List[BaseMessage]
    ) -> tuple[List[BaseMessage], str]:
        history = list(message_history) if message_history else []
        messages = history + [HumanMessage(content=user_input)]

        result = await asyncio.to_thread(self._graph.invoke, {"messages": messages})
        all_messages = result.get("messages", [])

        new_messages = all_messages[len(history) + 1 :]
        final_text = ""
        for msg in reversed(all_messages):
            if isinstance(msg, AIMessage) and msg.content:
                final_text = msg.content
                break

        return new_messages, final_text


class _AgentRunStream:
    def __init__(
        self, agent: WeatherAgent, user_input: str, message_history: List[BaseMessage]
    ) -> None:
        self._agent = agent
        self._user_input = user_input
        self._message_history = message_history
        self._new_messages: List[BaseMessage] = []
        self._final_text = ""

    async def __aenter__(self):
        self._new_messages, self._final_text = await self._agent._run(
            self._user_input, self._message_history
        )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def stream_text(self, delta: bool = True):
        for chunk in _iter_text_chunks(self._final_text):
            yield chunk
            await asyncio.sleep(0)

    def new_messages(self) -> List[BaseMessage]:
        return list(self._new_messages)


def _iter_text_chunks(text: str, chunk_size: int = 48):
    if not text:
        yield ""
        return

    for i in range(0, len(text), chunk_size):
        yield text[i : i + chunk_size]


def _build_model() -> ChatOpenAI:
    return ChatOpenAI(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        api_key=LLM_API_KEY,
        base_url=OLLAMA_BASE_URL,
    )


def build_agent() -> WeatherAgent:
    llm = _build_model()
    llm_with_tools = llm.bind_tools(WEATHER_TOOLS)

    def assistant(state: AgentState):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    graph = StateGraph(AgentState)
    graph.add_node("assistant", assistant)
    graph.add_node("tools", ToolNode(WEATHER_TOOLS))
    graph.add_conditional_edges("assistant", tools_condition)
    graph.add_edge("tools", "assistant")
    graph.set_entry_point("assistant")

    return WeatherAgent(graph.compile())
