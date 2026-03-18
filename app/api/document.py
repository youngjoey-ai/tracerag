from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.document import Document
from app.models.chunk import Chunk
from app.schemas.document import DocumentImportRequest
from app.services.chunking import split_text

router = APIRouter()
chunk_size = 200
chunk_overlap = 50

@router.post("/import")
def import_document(request: DocumentImportRequest, db: Session = Depends(get_db)):
    document = Document(
        title=request.title,
        content=request.content,
        source=request.source,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    chunks = split_text(
        request.content, 
        chunk_size=chunk_size, 
        chunk_overlap=chunk_overlap
    )

    chunk_objects = []
    for index, chunk_text in enumerate(chunks):
        chunk = Chunk(
            document_id=document.id,
            content=chunk_text,
            chunk_index=index,
            metadata_json={
                "document_title": document.title,
                "source": document.source,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
            },
        )
        chunk_objects.append(chunk)

    db.add_all(chunk_objects)
    db.commit()

    metadata = {
        "title_length": len(request.title),
        "content_length": len(request.content),
        "has_source": request.source is not None,
        "chunk_count": len(chunks),
        "avg_chunk_length": int(sum(len(c) for c in chunks) / len(chunks)) if chunks else 0,
    }

    return {
        "id": document.id,
        "title": document.title,
        "source": document.source,
        "metadata": metadata,
    }