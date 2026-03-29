import os
import requests
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

API_URL = "http://127.0.0.1:8000"
API_KEY = os.getenv("API_KEY", "")

st.title("TraceRAG")
st.caption("基于检索的问答系统")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander(f"来源（{len(msg['sources'])} 个片段）"):
                for s in msg["sources"]:
                    st.markdown(f"**{s['metadata_json'].get('document_title', '')}** chunk {s['chunk_index']}")
                    st.caption(s["content"])
        if msg.get("duration_ms") is not None:
            cached = " ⚡ cached" if msg.get("is_cached") else ""
            st.caption(f"{msg['duration_ms']}ms{cached}")

if prompt := st.chat_input("输入问题..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("检索中..."):
            try:
                r = requests.get(
                    f"{API_URL}/ask",
                    params={"q": prompt, "top_k": 3},
                    headers={"x-api-key": API_KEY},
                    timeout=60,
                )
                data = r.json()
                answer = data.get("answer", "")
                sources = data.get("sources", [])
                duration_ms = data.get("duration_ms")
                is_cached = data.get("is_cached", False)

                st.markdown(answer)
                if sources:
                    with st.expander(f"来源（{len(sources)} 个片段）"):
                        for s in sources:
                            st.markdown(f"**{s['metadata_json'].get('document_title', '')}** chunk {s['chunk_index']}")
                            st.caption(s["content"])
                cached_label = " ⚡ cached" if is_cached else ""
                st.caption(f"{duration_ms}ms{cached_label}")

            except Exception as e:
                answer = f"请求失败：{e}"
                sources = []
                duration_ms = None
                is_cached = False
                st.error(answer)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
        "duration_ms": duration_ms,
        "is_cached": is_cached,
    })