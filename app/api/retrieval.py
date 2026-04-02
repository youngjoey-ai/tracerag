from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import verify_api_key
from app.db.session import get_db
from app.services.retrieval import similarity_search

router = APIRouter()


@router.get("/retrieve", dependencies=[Depends(verify_api_key)])
def retrieve(
    q: str = Query(..., description="user query"),
    top_k: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db),
    source: str | None = Query(None)
):
    results = similarity_search(query=q, db=db, top_k=top_k, source=source)

    return {
        "query": q,
        "top_k": top_k,
        "results": results,
    }
