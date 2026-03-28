import os
import json
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

def score_answer(question: str, answer: str, contexts: list[str]) -> dict:
    context_text = "\n\n".join(contexts)
    prompt = f"""你是一个 RAG 系统评估专家。请根据以下信息对回答打分。

问题：{question}

检索到的上下文：
{context_text}

回答：{answer}

请从以下两个维度打分（0-1分，保留两位小数）：
1. faithfulness：回答是否完全基于上下文，没有编造信息
2. answer_relevance：回答是否真正回答了问题

只返回 JSON，格式如下：
{{"faithfulness": 0.95, "answer_relevance": 0.90, "reason": "简短理由"}}"""

    response = client.chat.completions.create(
        model="qwen-plus",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    
    text = response.choices[0].message.content
    return json.loads(text)

results_path = Path("eval/results.json")
results = json.loads(results_path.read_text(encoding="utf-8"))

scores = []
for item in results:
    contexts = [s["content"] for s in item["sources"]]
    score = score_answer(item["question"], item["answer"], contexts)
    score["question"] = item["question"]
    scores.append(score)
    print(f"Q: {item['question']}")
    print(f"   faithfulness: {score['faithfulness']}, answer_relevance: {score['answer_relevance']}")
    print(f"   reason: {score['reason']}")
    print()

avg_faithfulness = sum(s["faithfulness"] for s in scores) / len(scores)
avg_relevance = sum(s["answer_relevance"] for s in scores) / len(scores)
print(f"平均faithfulness: {avg_faithfulness:.2f}")
print(f"平均answer_relevance: {avg_relevance:.2f}")