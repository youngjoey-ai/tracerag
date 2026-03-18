from sqlalchemy.orm import Session

from app.models.document import Document
from app.schemas.document import DocumentImportRequest, DocumentImportResponse


def import_document(db: Session, data: DocumentImportRequest) -> DocumentImportResponse:
    document = Document(
        content=data.content,
        source=data.source,
        metadata_json=data.metadata,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return DocumentImportResponse(
        id=document.id,
        source=document.source,
        content_length=len(document.content),
        metadata=document.metadata_json or {},
        message="document imported successfully",
    )