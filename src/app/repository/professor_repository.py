from sqlalchemy import select
from sqlalchemy.orm import Session

from app.repository.models import Professor


class ProfessorRepository:
    def list_professors(self, db: Session, limit: int, offset: int) -> list[Professor]:
        stmt = select(Professor).order_by(Professor.id).limit(limit).offset(offset)
        return list(db.scalars(stmt))
