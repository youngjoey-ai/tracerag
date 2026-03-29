from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.embedding import process_document_embeddings

router = APIRouter()


@router.post("/embed/{document_id}")
def embed_document(document_id: int, db: Session = Depends(get_db)):
    """
    Generate and save embeddings for all chunks in a document.
    """
    return process_document_embeddings(document_id, db)
