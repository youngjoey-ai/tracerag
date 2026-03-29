from sqlalchemy.orm import Session
from langfuse import observe
from app.services.embedding import embed_texts
from app.repositories.chunk_repository import find_similar_chunks


@observe(name="retrieval")
def similarity_search(
    query: str,
    db: Session,
    top_k: int = 5,
    source: str | None = None,
) -> list[dict]:
    query_embedding = embed_texts([query])[0]
    return find_similar_chunks(db=db, query_embedding=query_embedding, top_k=top_k, source=source)