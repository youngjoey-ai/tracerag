from sqlalchemy import text
from sqlalchemy.orm import Session


def find_similar_chunks(
    db: Session,
    query_embedding: list[float],
    top_k: int,
    source: str | None = None,
) -> list[dict]:
    where_clauses = ["embedding IS NOT NULL"]
    params = {
        "query_embedding": str(query_embedding),
        "top_k": top_k,
    }

    if source is not None:
        where_clauses.append("metadata_json->>'source' = :source")
        params["source"] = source

    where_str = " AND ".join(where_clauses)

    sql_query = f"""
        SELECT
            id,
            document_id,
            chunk_index,
            content,
            metadata_json,
            embedding <=> CAST(:query_embedding AS vector) AS distance
        FROM chunks
        WHERE {where_str}
        ORDER BY embedding <=> CAST(:query_embedding AS vector)
        LIMIT :top_k
    """
    
    result = db.execute(text(sql_query), params)
    rows = result.mappings().all()

    return [
        {
            "id": row["id"],
            "document_id": row["document_id"],
            "chunk_index": row["chunk_index"],
            "content": row["content"],
            "metadata_json": row["metadata_json"],
            "distance": float(row["distance"]),
        }
        for row in rows
    ]

def find_bm25_chunks(
    db: Session,
    query: str,
    top_k: int,
) -> list[dict]:
    sql = text("""
        SELECT
            id,
            document_id,
            chunk_index,
            content,
            metadata_json,
            ts_rank(
                to_tsvector('simple', content),
                plainto_tsquery('simple', :query)
            ) AS score
        FROM chunks
        WHERE to_tsvector('simple', content) @@ plainto_tsquery('simple', :query)
        ORDER BY score DESC
        LIMIT :top_k
    """)
    result = db.execute(sql, {"query": query, "top_k": top_k})
    rows = result.mappings().all()
    return [
        {
            "id": row["id"],
            "document_id": row["document_id"],
            "chunk_index": row["chunk_index"],
            "content": row["content"],
            "metadata_json": row["metadata_json"],
            "score": float(row["score"]),
        }
        for row in rows
    ]