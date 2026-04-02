from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import verify_api_key
from app.db.session import get_db
from app.services.hybrid import hybrid_search

router = APIRouter()


@router.get("/retrieve_hybrid", dependencies=[Depends(verify_api_key)])
def retrieve_hybrid(
    q: str = Query(..., description="user query"),
    top_k: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db),
):
    results = hybrid_search(query=q, db=db, top_k=top_k)

    return {
        "query": q,
        "top_k": top_k,
        "results": results,
    }
