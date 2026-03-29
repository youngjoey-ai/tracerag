from sqlalchemy.orm import Session
import logging

from app.models.qa_log import QALog

logger = logging.getLogger(__name__)

def save_qa_log(db: Session, question: str, answer: str, duration_ms: int):
    try:
        qa_log = QALog(
            question=question,
            answer=answer,
            duration_ms=duration_ms,
        )
        db.add(qa_log)
        db.commit()
    except Exception:
        logger.exception("Failed to save QA Log to database.")
        db.rollback()
