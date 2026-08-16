from dataclasses import dataclass


class InvalidKnowledgeStatement(Exception):
    pass


@dataclass(frozen=True)
class KnowledgeStatement:
    """
    Immutable knowledge value owned by a LearningObject.

    KnowledgeStatement is an aggregate member/value.
    It has no independent identity, lifecycle, repository,
    or version history.
    """

    text: str
    language: str

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise InvalidKnowledgeStatement(
                "Statement text cannot be empty"
            )

        if not self.language.strip():
            raise InvalidKnowledgeStatement(
                "Statement language cannot be empty"
            )
