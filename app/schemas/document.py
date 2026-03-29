from pydantic import BaseModel

class DocumentImportRequest(BaseModel):
    title: str
    content: str
    source: str | None = None
    # 如果你确实想要 metadata，你需要在这里加上，比如：
    # metadata: dict | None = None

class DocumentImportResponse(BaseModel):
    id: int
    title: str
    source: str | None = None
    content_length: int
    message: str
