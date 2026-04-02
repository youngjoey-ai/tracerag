import os
import requests
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

API_URL = "http://127.0.0.1:8000"
API_KEY = os.getenv("API_KEY", "")
HEADERS = {"x-api-key": API_KEY} if API_KEY else {}


def render_sources(sources: list[dict]):
    if not sources:
        return

    with st.expander(f"来源（{len(sources)} 个片段）"):
        for source in sources:
            st.markdown(
                f"**{source['metadata_json'].get('document_title', '')}** chunk {source['chunk_index']}"
            )
            st.caption(source["content"])


def get_uploaded_text(uploaded_file) -> str:
    if uploaded_file is None:
        return ""

    return uploaded_file.getvalue().decode("utf-8")

st.title("TraceRAG")
st.caption("基于检索的问答系统")

with st.expander("手动导入文本", expanded=True):
    with st.form("manual_import_form"):
        import_mode = st.radio("导入方式", ["粘贴文本", "上传文件"], horizontal=True)
        uploaded_file = st.file_uploader("选择文件", type=["txt", "md"]) if import_mode == "上传文件" else None
        default_title = uploaded_file.name.rsplit(".", 1)[0] if uploaded_file else "手动上传文档"
        document_title = st.text_input("标题", value=default_title)
        document_source = st.text_input("来源", value="manual-upload")
        document_content = st.text_area(
            "文本内容",
            height=220,
            placeholder="在这里粘贴你要导入的文本",
            disabled=import_mode == "上传文件",
        )
        auto_embed = st.checkbox("导入后立即生成 embedding", value=True)
        submit_import = st.form_submit_button("导入文本")

    if submit_import:
        final_content = document_content if import_mode == "粘贴文本" else get_uploaded_text(uploaded_file)
        final_title = document_title.strip() or default_title

        if not final_content.strip():
            st.error("请输入要导入的文本内容。")
        else:
            with st.spinner("正在导入文本..."):
                try:
                    import_response = requests.post(
                        f"{API_URL}/import",
                        json={
                            "title": final_title,
                            "content": final_content,
                            "source": document_source.strip() or None,
                        },
                        headers=HEADERS,
                        timeout=60,
                    )
                    import_response.raise_for_status()
                    imported = import_response.json()
                    document_id = imported["id"]

                    chunk_count = imported.get("metadata", {}).get("chunk_count")
                    st.success(f"导入成功，document_id={document_id}，chunk_count={chunk_count}")

                    if auto_embed:
                        embed_response = requests.post(
                            f"{API_URL}/embed/{document_id}",
                            headers=HEADERS,
                            timeout=120,
                        )
                        embed_response.raise_for_status()
                        embedded = embed_response.json()
                        st.success(
                            f"Embedding 生成完成，维度={embedded.get('embedding_dimension')}，chunk_count={embedded.get('chunk_count')}"
                        )
                except requests.HTTPError as exc:
                    response = exc.response
                    detail = response.text if response is not None else str(exc)
                    st.error(f"导入失败：{detail}")
                except UnicodeDecodeError:
                    st.error("文件解析失败：请上传 UTF-8 编码的 .txt 或 .md 文件。")
                except Exception as exc:
                    st.error(f"导入失败：{exc}")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        render_sources(msg.get("sources", []))
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
                    headers=HEADERS,
                    timeout=60,
                )
                r.raise_for_status()
                data = r.json()
                answer = data.get("answer", "")
                sources = data.get("sources", [])
                duration_ms = data.get("duration_ms")
                is_cached = data.get("is_cached", False)

                st.markdown(answer)
                render_sources(sources)
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
