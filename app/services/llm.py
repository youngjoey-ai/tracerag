import os
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from langfuse import Langfuse, observe

from app.core.config import LLM_BASE_URL, LLM_MODEL

_cached_system_prompt = None

def get_system_prompt() -> str:
    global _cached_system_prompt
    if _cached_system_prompt is None:
        langfuse = Langfuse()
        _cached_system_prompt = langfuse.get_prompt("rag-system-prompt").get_langchain_prompt()[0][1]
    return _cached_system_prompt

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=LLM_BASE_URL,
)

@observe(name="generation")
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
)
def generate_answer(prompt: str) -> str:
    system_prompt_text = get_system_prompt()
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system", 
                "content": system_prompt_text,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content

@observe(name="query_rewrite")
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
)
def rewrite_query(query: str) -> str:
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": "你是一个专业的查询改写助手。你的任务是将用户的问题改写成更适合检索的关键词形式。要求：1. 提取核心概念和关键词 2. 去除无关的修饰词 3. 保持原意 4. 只输出改写后的关键词，不要任何解释",
            },
            {
                "role": "user",
                "content": f"请将以下问题改写成适合检索的关键词：\n\n{query}",
            },
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content
