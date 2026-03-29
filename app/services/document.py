from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.chunk import Chunk
from app.schemas.document import DocumentImportRequest, DocumentImportResponse
from app.services.chunking import split_text
from app.core.config import CHUNK_SIZE, CHUNK_OVERLAP


def import_document(db: Session, data: DocumentImportRequest) -> DocumentImportResponse:
    document = Document(
        title=data.title,
        content=data.content,
        source=data.source,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    chunks = split_text(
        data.content,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
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
                "chunk_size": CHUNK_SIZE,
                "chunk_overlap": CHUNK_OVERLAP,
            },
        )
        chunk_objects.append(chunk)

    db.add_all(chunk_objects)
    db.commit()

    metadata = {
        "title_length": len(data.title),
        "content_length": len(data.content),
        "has_source": data.source is not None,
        "chunk_count": len(chunks),
        "avg_chunk_length": int(sum(len(c) for c in chunks) / len(chunks)) if chunks else 0,
    }

    return DocumentImportResponse(
        id=document.id,
        title=document.title,
        source=document.source,
        metadata=metadata,
    )