from pydantic import BaseModel


class DocumentImportRequest(BaseModel):
    title: str
    content: str
    source: str | None = None