from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from env_loader import load_lab_env
from providers import make_provider
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version
from chat import (
    now_iso,
    safe_slug,
    trim_history,
    run_model_tool_loop,
    write_transcript,
)

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
load_lab_env(ROOT)

st.set_page_config(
    page_title="AI Research Agent — UI",
    page_icon="🤖",
    layout="wide",
)

# Custom header
st.title("🤖 AI Research Agent")
st.caption("Day 03 Lab — Evidence-driven Research Agent with Live Tool Calling")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Agent Settings")
    provider_name = st.selectbox(
        "Model Provider",
        options=["openrouter", "openai", "anthropic", "gemini", "ollama"],
        index=0,
    )
    version_label = st.selectbox(
        "Prompt & Tool Version",
        options=["v0", "v1", "v2", "v3"],
        index=0,
    )
    custom_model = st.text_input("Custom Model (optional)", value="", placeholder="Leave empty for provider default")
    model_name = custom_model.strip() or None

    max_tool_rounds = st.slider("Max Tool Rounds", min_value=1, max_value=8, value=4)
    history_window = st.slider("History Window (turns)", min_value=1, max_value=10, value=5)

    st.divider()
    st.markdown("### 🛠️ Available Tools")
    try:
        tools_decl = load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")
        for t in tools_decl:
            name = t.get("name", "unnamed")
            desc = t.get("description", "")
            summary = desc[:60] + "..." if len(desc) > 60 else desc
            st.markdown(f"- **`{name}`**: {summary}")
    except Exception as e:
        st.error(f"Error loading tools: {e}")

    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.session_state.history = []
        st.session_state.transcript = None
        st.rerun()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []
if "transcript" not in st.session_state:
    st.session_state.transcript = None
if "transcript_path" not in st.session_state:
    st.session_state.transcript_path = None

# Initialize transcript session if not yet initialized
if st.session_state.transcript is None:
    system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
    tools_path = ARTIFACTS_DIR / "tools.yaml"
    artifact_version = build_artifact_version(version_label, system_prompt_path, tools_path)
    
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([
        safe_slug(version_label),
        safe_slug(provider_name),
        timestamp,
    ])
    transcript_path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"
    st.session_state.transcript_path = transcript_path
    st.session_state.transcript = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": provider_name,
        "model": model_name,
        "system_prompt": str(system_prompt_path),
        "tools": str(tools_path),
        "history_window": history_window,
        "max_tool_rounds": max_tool_rounds,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }

# Display existing messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("tool_events"):
            with st.expander(f"🔧 Tool Calls ({len(msg['tool_events'])})", expanded=False):
                for event in msg["tool_events"]:
                    st.markdown(f"**Tool:** `{event.get('tool')}`")
                    st.json(event.get("args"), expanded=False)
                    st.markdown("**Result:**")
                    st.json(event.get("result"), expanded=False)
                    st.divider()
        st.markdown(msg["content"])

# User Chat Input
if prompt := st.chat_input("Hỏi research agent hoặc yêu cầu tìm kiếm, tổng hợp..."):
    # Render user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepare agent run
    system_prompt = (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
    tool_declarations = load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")
    openai_tools = to_openai_tools(tool_declarations)
    provider = make_provider(provider_name)

    conversation_messages = [
        {"role": "system", "content": system_prompt},
        *trim_history(st.session_state.history, history_window),
        {"role": "user", "content": prompt},
    ]

    turn_index = len(st.session_state.transcript["turns"]) + 1
    turn_record = {
        "turn_index": turn_index,
        "started_at": now_iso(),
        "user": prompt,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }

    with st.chat_message("assistant"):
        with st.spinner("Agent đang suy nghĩ và gọi tools..."):
            try:
                result = run_model_tool_loop(
                    provider=provider,
                    messages=conversation_messages,
                    tools=openai_tools,
                    model=model_name,
                    max_tool_rounds=max_tool_rounds,
                )
                turn_record.update(result)
                assistant_text = result["assistant_text"]

                # Render tool calls if any
                tool_events = result.get("tool_events", [])
                if tool_events:
                    with st.expander(f"🔧 Tool Execution Log ({len(tool_events)})", expanded=True):
                        for event in tool_events:
                            tool_name = event.get("tool")
                            st.markdown(f"**Called:** `{tool_name}`")
                            st.caption(f"Arguments: `{json.dumps(event.get('args', {}), ensure_ascii=False)}`")
                            with st.expander(f"Output of `{tool_name}`", expanded=False):
                                st.json(event.get("result", {}))

                st.markdown(assistant_text)

                # Save history
                st.session_state.history.append({"role": "user", "content": prompt})
                st.session_state.history.append({"role": "assistant", "content": assistant_text})
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_text,
                    "tool_events": tool_events,
                })

            except Exception as exc:
                err_msg = f"{type(exc).__name__}: {str(exc)}"
                turn_record.update({
                    "status": "provider_error",
                    "error": err_msg,
                })
                st.error(f"❌ Error: {err_msg}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Lỗi: {err_msg}",
                    "tool_events": [],
                })

        turn_record["ended_at"] = now_iso()
        st.session_state.transcript["turns"].append(turn_record)
        write_transcript(st.session_state.transcript_path, st.session_state.transcript)

