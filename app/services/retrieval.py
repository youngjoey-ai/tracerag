from sqlalchemy import text
from sqlalchemy.orm import Session
from langfuse import observe
from app.services.embedding import embed_texts


@observe(name="retrieval")
def similarity_search(
    query: str,
    db: Session,
    top_k: int = 5,
    source: str | None = None,
) -> list[dict]:
    query_embedding = embed_texts([query])[0]

    if source is None:
        sql = text("""
            SELECT
                id,
                document_id,
                chunk_index,
                content,
                metadata_json,
                embedding <=> CAST(:query_embedding AS vector) AS distance
            FROM chunks
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> CAST(:query_embedding AS vector)
            LIMIT :top_k
        """)

        result = db.execute(
            sql,
            {
                "query_embedding": str(query_embedding),
                "top_k": top_k,
            },
        )
    else:
        sql = text("""
            SELECT
                id,
                document_id,
                chunk_index,
                content,
                metadata_json,
                embedding <=> CAST(:query_embedding AS vector) AS distance
            FROM chunks
            WHERE embedding IS NOT NULL
              AND metadata_json->>'source' = :source
            ORDER BY embedding <=> CAST(:query_embedding AS vector)
            LIMIT :top_k
        """)

        result = db.execute(
            sql,
            {
                "query_embedding": str(query_embedding),
                "top_k": top_k,
                "source": source,
            },
        )

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