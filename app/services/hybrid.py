from sqlalchemy.orm import Session

from app.services.retrieval import similarity_search
from app.repositories.chunk_repository import find_bm25_chunks


def bm25_search(query: str, db: Session, top_k: int = 5) -> list[dict]:
    return find_bm25_chunks(db=db, query=query, top_k=top_k)


def rrf_fuse(vector_results: list[dict], bm25_results: list[dict], k: int = 60) -> list[dict]:
    fused_scores = {}

    for rank, item in enumerate(vector_results, start=1):
        key = item["id"]
        fused_scores.setdefault(key, {"item": item, "score": 0.0})
        fused_scores[key]["score"] += 1 / (k + rank)

    for rank, item in enumerate(bm25_results, start=1):
        key = item["id"]
        fused_scores.setdefault(key, {"item": item, "score": 0.0})
        fused_scores[key]["score"] += 1 / (k + rank)

    fused = [
        {
            **value["item"],
            "rrf_score": value["score"],
        }
        for value in fused_scores.values()
    ]

    fused.sort(key=lambda x: x["rrf_score"], reverse=True)
    return fused


def simple_rerank(query: str, results: list[dict]) -> list[dict]:
    query_terms = [term.strip().lower() for term in query.split() if term.strip()]

    def keyword_overlap_score(item: dict) -> int:
        content = item["content"].lower()
        return sum(1 for term in query_terms if term in content)

    reranked = []
    for item in results:
        item = {**item, "rerank_score": keyword_overlap_score(item)}
        reranked.append(item)

    reranked.sort(key=lambda x: (x["rerank_score"], x.get("rrf_score", 0)), reverse=True)
    return reranked


def hybrid_search(query: str, db: Session, top_k: int = 5) -> list[dict]:
    vector_results = similarity_search(query=query, db=db, top_k=top_k)
    bm25_results = bm25_search(query=query, db=db, top_k=top_k)

    fused = rrf_fuse(vector_results, bm25_results)
    reranked = simple_rerank(query, fused)

    return reranked[:top_k]