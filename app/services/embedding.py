import os
from openai import OpenAI
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.core.config import LLM_BASE_URL, EMBEDDING_MODEL
from app.models.chunk import Chunk

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=LLM_BASE_URL,
)


def embed_texts(texts: list[str]) -> list[list[float]]:
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
        dimensions=1536,
    )
    return [item.embedding for item in response.data]


def process_document_embeddings(document_id: int, db: Session) -> dict:
    chunks = (
        db.query(Chunk)
        .filter(Chunk.document_id == document_id)
        .order_by(Chunk.chunk_index.asc())
        .all()
    )

    if not chunks:
        raise HTTPException(status_code=404, detail="No chunks found for this document")

    texts = [chunk.content for chunk in chunks]
    embeddings = embed_texts(texts)

    if len(chunks) != len(embeddings):
        raise HTTPException(status_code=500, detail="Embedding count mismatch")

    for chunk, embedding in zip(chunks, embeddings):
        chunk.embedding = embedding

    db.commit()

    return {
        "document_id": document_id,
        "chunk_count": len(chunks),
        "embedding_dimension": len(embeddings[0]) if embeddings else 0,
        "status": "ok",
    }
