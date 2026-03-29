def build_prompt(query: str, results: list[dict]) -> str:
    context_blocks = []

    for i, item in enumerate(results, start=1):
        block = f"""[片段 {i}]
document_id: {item["document_id"]}
chunk_index: {item["chunk_index"]}
content: {item["content"]}
"""
        context_blocks.append(block)

    context_text = "\n\n".join(context_blocks)

    context_text = context_text[:3000]

    return f"""请基于下面提供的上下文回答问题。

如果上下文足够，请给出简洁、准确的答案。
如果上下文不足，请明确说“根据当前检索到的资料，无法确定”。

问题：
{query}

上下文：
{context_text}
"""