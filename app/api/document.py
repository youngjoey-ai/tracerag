from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import verify_api_key
from app.db.session import get_db
from app.schemas.document import DocumentImportRequest, DocumentImportResponse
from app.services.document import import_document as svc_import_document

router = APIRouter()

@router.post("/import", response_model=DocumentImportResponse, dependencies=[Depends(verify_api_key)])
def import_document(request: DocumentImportRequest, db: Session = Depends(get_db)):
    """
    Import a document, chunk it and save to database.
    """
    return svc_import_document(db, request)
