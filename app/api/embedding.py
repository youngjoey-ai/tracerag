from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.chunk import Chunk
from app.services.embedding import embed_texts

router = APIRouter()


@router.post("/embed/{document_id}")
def embed_document(document_id: int, db: Session = Depends(get_db)):
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
