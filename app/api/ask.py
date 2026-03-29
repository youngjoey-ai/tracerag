from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from langfuse import observe
import time

from app.cache import get_cache, set_cache
from app.db.session import get_db
from app.services.graph import build_ask_graph
from app.services.qa_log import save_qa_log
from app.core.auth import verify_api_key

router = APIRouter()


@router.get("/ask", dependencies=[Depends(verify_api_key)])
@observe(name="ask")
def ask(
    background_tasks: BackgroundTasks,
    q: str = Query(..., description="user question"),
    top_k: int = Query(3, ge=1, le=10),
    db: Session = Depends(get_db),
):
    start_time = time.perf_counter()

    cache_key = f"ask:q={q}:top_k={top_k}"
    cached = get_cache(cache_key)
    
    if cached:
        result = cached
        result["is_cached"] = True
    else:
        graph = build_ask_graph(db)
        state = graph.invoke({"query": q, "top_k": top_k, "results": [], "answer": ""})

        sources = [
            {
                "document_id": item["document_id"],
                "chunk_index": item["chunk_index"],
                "content": item["content"],
                "metadata_json": item["metadata_json"],
                "distance": item["distance"],
            }
            for item in state["results"]
        ]

        result = {
            "query": q,
            "answer": state["answer"],
            "sources": sources,
        }
        set_cache(cache_key, result)

    result["duration_ms"] = int((time.perf_counter() - start_time) * 1000)
    
    # Save the interaction to PostgreSQL seamlessly in the background!
    background_tasks.add_task(save_qa_log, db, result["query"], result["answer"], result["duration_ms"])
    
    return result