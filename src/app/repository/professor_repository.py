from sqlalchemy import select
from sqlalchemy.orm import Session

from app.repository.models import Professor


class ProfessorRepository:
    def list_professors(self, db: Session, limit: int, cursor: int | None) -> list[Professor]:
        stmt = select(Professor)
        if cursor is not None:
            stmt = stmt.where(Professor.id > cursor)
        stmt = stmt.order_by(Professor.id).limit(limit + 1)
        return list(db.scalars(stmt))
