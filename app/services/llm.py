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
