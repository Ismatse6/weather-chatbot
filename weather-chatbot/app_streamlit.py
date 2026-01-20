from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List

import streamlit as st
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage

from core.agent.agent import build_agent

# ========= Helpers UI =========


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Source+Serif+4:wght@400;600&display=swap');

        :root {
            --bg-1: #f7f2eb;
            --bg-2: #dbeffd;
            --ink: #0f2b36;
            --muted: #4f6b75;
            --accent: #1d6a7c;
            --accent-2: #f29f3d;
            --card: rgba(255, 255, 255, 0.75);
            --border: #d7e3ea;
        }

        .stApp {
            background:
                radial-gradient(1200px 600px at 10% -10%, #ffe7c6 0%, transparent 60%),
                radial-gradient(800px 400px at 90% 10%, #c7f1ff 0%, transparent 55%),
                linear-gradient(180deg, var(--bg-1), var(--bg-2));
            color: var(--ink);
        }

        .stApp::before,
        .stApp::after {
            content: "";
            position: fixed;
            border-radius: 50%;
            z-index: 0;
            filter: blur(12px);
            opacity: 0.2;
            animation: float 12s ease-in-out infinite;
        }

        .stApp::before {
            top: -140px;
            right: -140px;
            width: 360px;
            height: 360px;
            background: radial-gradient(circle at 30% 30%, #ffd5a4, #f6a552);
        }

        .stApp::after {
            bottom: -160px;
            left: -120px;
            width: 420px;
            height: 420px;
            background: radial-gradient(circle at 30% 30%, #a6e6ff, #4ab7d8);
            animation-direction: reverse;
        }

        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(16px); }
            100% { transform: translateY(0px); }
        }

        section.main .block-container {
            max-width: 1200px;
            padding-top: 2.5rem;
            position: relative;
            z-index: 1;
        }

        h1, h2, h3, h4, .hero-title {
            font-family: "Space Grotesk", sans-serif;
            letter-spacing: -0.02em;
        }

        .stMarkdown, .stChatMessage, .stTextInput, .stButton, .stCaption {
            font-family: "Source Serif 4", serif;
            color: var(--ink);
        }

        .hero {
            display: flex;
            flex-wrap: wrap;
            gap: 2rem;
            align-items: flex-start;
            padding: 1.75rem 2rem;
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 24px;
            box-shadow: 0 20px 40px rgba(15, 43, 54, 0.12);
            backdrop-filter: blur(10px);
            animation: rise 0.8s ease-out;
        }

        @keyframes rise {
            from { opacity: 0; transform: translateY(16px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .hero-text {
            flex: 1 1 320px;
        }

        .hero-text h1 {
            margin: 0.3rem 0 0.6rem;
            font-size: 2.4rem;
        }

        .hero-text p {
            margin: 0;
            color: var(--muted);
            font-size: 1.05rem;
        }

        .pill {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.35rem 0.75rem;
            border-radius: 999px;
            background: var(--ink);
            color: #fff;
            font-size: 0.75rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }

        .hero-cards {
            flex: 1 1 280px;
            display: grid;
            gap: 0.9rem;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        }

        .stat-card {
            padding: 1rem 1.1rem;
            background: rgba(255, 255, 255, 0.8);
            border: 1px solid var(--border);
            border-radius: 16px;
            box-shadow: 0 10px 20px rgba(15, 43, 54, 0.08);
        }

        .stat-label {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: var(--muted);
        }

        .stat-value {
            display: block;
            margin-top: 0.4rem;
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--ink);
        }

        .section-title {
            margin: 2rem 0 0.6rem;
            font-size: 1.05rem;
            font-weight: 600;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.14em;
        }

        .sidebar-card {
            padding: 1rem;
            background: rgba(255, 255, 255, 0.7);
            border: 1px solid var(--border);
            border-radius: 14px;
            margin-bottom: 1rem;
        }

        .stButton > button {
            background: var(--accent) !important;
            color: #fff !important;
            border: none !important;
            border-radius: 14px;
            padding: 0.6rem 1rem;
            font-weight: 600;
            letter-spacing: 0.02em;
            transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
        }

        .stButton > button:hover,
        .stButton > button:focus,
        .stButton > button:active {
            background: #195d6d !important;
            color: #fff !important;
            transform: translateY(-1px);
            box-shadow: 0 10px 20px rgba(29, 106, 124, 0.25);
        }

        div[data-testid="stChatMessage"] {
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 0.75rem 1rem;
            box-shadow: 0 10px 24px rgba(15, 43, 54, 0.08);
        }

        div[data-testid="stChatInput"] textarea {
            border-radius: 16px;
            border: 1px solid var(--border);
            padding: 0.75rem 1rem;
            background: rgba(255, 255, 255, 0.9);
            color: var(--ink);
            caret-color: var(--ink);
        }

        div[data-testid="stChatInput"] textarea::placeholder {
            color: var(--muted);
        }

        div[data-testid="stExpander"] {
            border: 1px solid var(--border);
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.65);
        }

        div[data-testid="stExpander"] > details {
            background: transparent;
        }

        div[data-testid="stExpander"] summary {
            background: rgba(255, 255, 255, 0.9);
            color: var(--ink);
            border-radius: 12px;
            padding: 0.5rem 0.75rem;
        }

        div[data-testid="stExpander"] summary:hover {
            background: rgba(241, 246, 248, 0.95);
        }

        div[data-testid="stExpander"] summary svg {
            color: var(--ink);
            fill: var(--ink);
        }

        div[data-testid="stCodeBlock"] {
            background: rgba(244, 247, 249, 0.95);
            border: 1px solid var(--border);
            border-radius: 12px;
        }

        div[data-testid="stCodeBlock"] pre,
        div[data-testid="stCodeBlock"] code {
            color: var(--ink);
        }

        div[data-testid="stSpinner"] {
            color: var(--accent);
        }

        div[data-testid="stSpinner"] svg {
            stroke: var(--accent);
            fill: var(--accent);
        }

        .footer {
            margin-top: 2.5rem;
            padding: 1rem 1.2rem;
            border-top: 1px solid var(--border);
            color: var(--muted);
            font-size: 0.9rem;
            text-align: center;
        }

        @media (max-width: 900px) {
            .hero {
                padding: 1.5rem;
            }

            .hero-text h1 {
                font-size: 2rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_hero() -> None:
    st.markdown(
        """
        <div class="hero">
            <div class="hero-text">
                <div class="pill">Live weather intelligence</div>
                <h1>Weather Briefing Studio</h1>
                <p>
                    Professional weather assistant for current conditions and forecasts.
                    Ask about any city to get temperature in Celsius, humidity, wind in kph,
                    and air quality metrics.
                </p>
            </div>
            <div class="hero-cards">
                <div class="stat-card">
                    <span class="stat-label">Mode</span>
                    <span class="stat-value">Weather only</span>
                </div>
                <div class="stat-card">
                    <span class="stat-label">Tools</span>
                    <span class="stat-value">Current + Forecast</span>
                </div>
                <div class="stat-card">
                    <span class="stat-label">Air quality</span>
                    <span class="stat-value">Always on</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
    st.set_page_config(page_title="Weather Briefing Studio", page_icon="W", layout="wide")
    _inject_styles()
    _render_hero()

    with st.sidebar:
        st.header("Weather Chatbot")
        st.caption("Live weather and air quality assistant.")
        st.markdown(
            """
            <div class="sidebar-card">
                <strong>Data source</strong><br/>
                WeatherAPI current and forecast endpoints.
            </div>
            <div class="sidebar-card">
                <strong>Units</strong><br/>
                Temperature: C<br/>
                Wind: kph<br/>
                Humidity: percent
            </div>
            """,
            unsafe_allow_html=True,
        )
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

    st.markdown('<div class="section-title">Quick prompts</div>', unsafe_allow_html=True)
    quick_prompt = None
    quick_cols = st.columns(3)
    if quick_cols[0].button("Current weather in Madrid", use_container_width=True):
        quick_prompt = "What is the current weather in Madrid?"
    if quick_cols[1].button("3-day forecast in Barcelona", use_container_width=True):
        quick_prompt = "Give me the 3 day forecast for Barcelona."
    if quick_cols[2].button("Air quality in Valencia", use_container_width=True):
        quick_prompt = "How is the air quality in Valencia right now?"

    st.markdown('<div class="section-title">Conversation</div>', unsafe_allow_html=True)
    _render_turns()

    user_input = st.chat_input("Type your question...")
    if quick_prompt:
        user_input = quick_prompt

    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)
        await stream_agent_reply(user_input)

    st.markdown(
        '<div class="footer">Authors: Daniel Acosta Luna and Ismael Tse Perdomo Rodriguez</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    asyncio.run(main())
