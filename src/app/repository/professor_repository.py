"""Professor persistence queries."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.repository.models import Professor


class ProfessorRepository:
    """Data access object for professor entities."""

    def list_professors(self, db: Session, limit: int, cursor: int | None) -> list[Professor]:
        """Fetch professor rows ordered by ID with cursor pagination."""
        stmt = select(Professor)
        if cursor is not None:
            stmt = stmt.where(Professor.id > cursor)
        stmt = stmt.order_by(Professor.id).limit(limit + 1)
        return list(db.scalars(stmt))
