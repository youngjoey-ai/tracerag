import time
from app.cache import get_cache, set_cache

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from langfuse import observe

from app.db.session import get_db
from app.services.retrieval import similarity_search
from app.services.llm import build_prompt, generate_answer

router = APIRouter()


@router.get("/ask")
@observe(name="ask")
def ask(
    q: str = Query(..., description="user question"),
    top_k: int = Query(3, ge=1, le=10),
    db: Session = Depends(get_db),
):
    start_time = time.perf_counter()

    cache_key = f"ask:q={q}:top_k={top_k}"
    cached = get_cache(cache_key)
    if cached:
        cached["duration_ms"] = int((time.perf_counter() - start_time) * 1000)
        cached["is_cached"] = True
        return cached

    results = similarity_search(query=q, db=db, top_k=top_k)

    if not results:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        return {
            "query": q,
            "answer": "根据当前检索到的资料，无法确定答案。",
            "sources": [],
            "duration_ms": duration_ms,
        }
    
    prompt = build_prompt(query=q, results=results)
    try:
        answer = generate_answer(prompt)
    except Exception:
        answer = "抱歉，当前生成答案时出现异常，请稍后重试。"

    duration_ms = int((time.perf_counter() - start_time) * 1000)

    sources = [
        {
            "document_id": item["document_id"],
            "chunk_index": item["chunk_index"],
            "content": item["content"],
            "metadata_json": item["metadata_json"],
            "distance": item["distance"],
        }
        for item in results
    ]

    result = {
        "query": q,
        "answer": answer,
        "sources": sources,
        "duration_ms": duration_ms,
    }

    set_cache(cache_key, result)
    return result