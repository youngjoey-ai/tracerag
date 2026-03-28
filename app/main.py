from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from app.api.document import router as document_router
from app.api.embedding import router as embedding_router
from app.api.retrieval import router as retrieval_router
from app.api.ask import router as ask_router
from app.api.hybrid import router as hybrid_router

app = FastAPI()

app.include_router(document_router)
app.include_router(embedding_router)
app.include_router(retrieval_router)
app.include_router(ask_router)
app.include_router(hybrid_router)


@app.get("/health")
def health():
    return {"status": "ok"}