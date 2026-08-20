from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.domain.entities.review_decision import ReviewDecision
from app.domain.entities.review_decision_trace import (
    ReviewDecisionTrace,
)
from app.persistence.models.base import Base
from app.persistence.repositories.review_decision_trace_repository import (
    SQLAlchemyReviewDecisionTraceRepository,
)


def create_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionFactory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    return engine, SessionFactory()


def test_add_and_get_by_id_review_decision_trace():
    engine, session = create_session()

    try:
        proposal_id = uuid4()

        trace = ReviewDecisionTrace(
            proposal_id=proposal_id,
            decision=ReviewDecision.APPROVE,
            rationale="Proposal is valid.",
            reviewer="learning-review",
            created_at=datetime.now(timezone.utc),
        )

        repository = SQLAlchemyReviewDecisionTraceRepository(
            session
        )

        repository.add(trace)
        session.flush()

        loaded = repository.get_by_id(trace.id)

        assert loaded is not None
        assert loaded.id == trace.id
        assert loaded.proposal_id == proposal_id
        assert loaded.decision is ReviewDecision.APPROVE
        assert loaded.rationale == "Proposal is valid."
        assert loaded.reviewer == "learning-review"
        assert loaded.created_at == trace.created_at
    finally:
        session.rollback()
        session.close()
        engine.dispose()


def test_get_by_proposal_id_returns_traces_in_creation_order():
    engine, session = create_session()

    try:
        proposal_id = uuid4()

        first = ReviewDecisionTrace(
            proposal_id=proposal_id,
            decision=ReviewDecision.REQUEST_REVISION,
            rationale="Revision required.",
            reviewer="learning-review",
            created_at=datetime(
                2026,
                1,
                1,
                tzinfo=timezone.utc,
            ),
        )

        second = ReviewDecisionTrace(
            proposal_id=proposal_id,
            decision=ReviewDecision.APPROVE,
            rationale="Revision accepted.",
            reviewer="learning-review",
            created_at=datetime(
                2026,
                1,
                2,
                tzinfo=timezone.utc,
            ),
        )

        repository = SQLAlchemyReviewDecisionTraceRepository(
            session
        )

        repository.add(second)
        repository.add(first)
        session.flush()

        traces = repository.get_by_proposal_id(proposal_id)

        assert [trace.id for trace in traces] == [
            first.id,
            second.id,
        ]
        assert traces[0].decision is ReviewDecision.REQUEST_REVISION
        assert traces[1].decision is ReviewDecision.APPROVE
    finally:
        session.rollback()
        session.close()
        engine.dispose()
