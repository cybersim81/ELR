from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.orm import Session

from app.persistence.database import SessionFactory


@contextmanager
def transaction(
    session: Session | None = None,
) -> Iterator[Session]:
    owned_session = session is None
    session = session or SessionFactory()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        if owned_session:
            session.close()
