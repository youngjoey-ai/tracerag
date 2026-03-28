import os
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from langfuse import Langfuse, observe

langfuse = Langfuse()
system_prompt = langfuse.get_prompt("rag-system-prompt").get_langchain_prompt()[0][1]

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

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

@observe(name="generation")
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
)
def generate_answer(prompt: str) -> str:
    response = client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {
                "role": "system", 
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content
