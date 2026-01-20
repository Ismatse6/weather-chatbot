from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List

import streamlit as st
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage

from core.agent.agent import build_agent

# ========= Helpers UI =========


def _render_details(details: List[Dict[str, Any]]) -> None:
    for d in details:
        kind = d.get("kind")
        name = d.get("name", "tool")
        if kind == "tool-call":
            st.markdown(f"Tool call: `{name}`")
            args = d.get("args")
            if args is not None:
                st.code(
                    json.dumps(args, ensure_ascii=False, indent=2)
                    if isinstance(args, (dict, list))
                    else str(args),
                    language="json",
                )
        elif kind == "tool-return":
            st.markdown(f"Tool return: `{name}`")
            content = d.get("content")
            if content is not None:
                st.code(
                    json.dumps(content, ensure_ascii=False, indent=2)
                    if isinstance(content, (dict, list))
                    else str(content),
                    language="json",
                )


def _extract_tool_details(new_msgs: List[BaseMessage]) -> List[Dict[str, Any]]:
    details: List[Dict[str, Any]] = []
    for m in new_msgs:
        if isinstance(m, AIMessage):
            tool_calls = getattr(m, "tool_calls", None)
            if tool_calls:
                for call in tool_calls:
                    if isinstance(call, dict):
                        name = call.get("name", "tool")
                        args = call.get("args")
                    else:
                        name = getattr(call, "name", "tool")
                        args = getattr(call, "args", None)
                    details.append({"kind": "tool-call", "name": name, "args": args})
        elif isinstance(m, ToolMessage):
            name = getattr(m, "name", None) or getattr(m, "tool_call_id", "tool")
            details.append(
                {"kind": "tool-return", "name": name, "content": m.content}
            )
    return details


def _render_turns() -> None:
    """Render the consolidated history (ui_turns)."""
    for turn in st.session_state.ui_turns:
        with st.chat_message("user"):
            st.markdown(turn["user"])
        with st.chat_message("assistant"):
            st.markdown(turn["assistant"])
            if turn["details"]:
                with st.container():
                    with st.expander(
                        f"Tool details ({len(turn['details'])})", expanded=False
                    ):
                        _render_details(turn["details"])


# ========= Streaming =========


async def stream_agent_reply(user_input: str) -> None:
    st.session_state.chat_history.append(HumanMessage(content=user_input))

    live_block = st.empty()

    details: List[Dict[str, Any]] = []

    with live_block.container():
        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                text_placeholder = st.empty()
                details_placeholder = st.empty()
                partial = ""

                async with st.session_state.agent.run_stream(
                    user_input,
                    message_history=st.session_state.chat_history[:-1],
                ) as result:
                    async for delta in result.stream_text(delta=True):
                        partial += delta
                        text_placeholder.markdown(partial)

                    new_msgs = result.new_messages()
                    st.session_state.chat_history.extend(new_msgs)

                    details = _extract_tool_details(new_msgs)
                    if details:
                        with details_placeholder.container():
                            with st.expander(
                                f"Tool details ({len(details)})", expanded=False
                            ):
                                _render_details(details)

    assistant_text = partial.strip()
    st.session_state.ui_turns.append(
        {
            "user": user_input,
            "assistant": assistant_text,
            "details": details,
        }
    )

    live_block.empty()
    st.rerun()


# ========= Main =========


async def main():
    st.set_page_config(page_title="Weather Chat", page_icon="W", layout="wide")
    st.title("Weather Chat")

    with st.sidebar:
        st.header("Description")
        st.caption("Chatbot for current weather and forecasts.")
        if st.button("Reset conversation"):
            st.session_state.chat_history = []
            st.session_state.ui_turns = []
            st.rerun()

    if "agent" not in st.session_state:
        st.session_state.agent = build_agent()
    if "chat_history" not in st.session_state:
        st.session_state.chat_history: List[BaseMessage] = []
    if "ui_turns" not in st.session_state:
        st.session_state.ui_turns: List[Dict[str, Any]] = []

    _render_turns()

    user_input = st.chat_input("Type your question...")
    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)
        await stream_agent_reply(user_input)


if __name__ == "__main__":
    asyncio.run(main())
