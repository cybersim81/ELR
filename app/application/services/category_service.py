from __future__ import annotations

from app.domain.entities.knowledge_category import KnowledgeCategory
from app.domain.repositories.category_repository import CategoryRepository


class CategoryService:
    """Application service for Knowledge Category operations."""

    def __init__(self, category_repository: CategoryRepository) -> None:
        self._category_repository = category_repository

    def get_categories(self) -> list[KnowledgeCategory]:
        """Return all persisted knowledge categories."""
        return self._category_repository.get_all()

    def get_category_tree(self) -> list[dict]:
        """Return categories organized according to their parent_id."""
        categories = self._category_repository.get_all()

        nodes = {
            category.id: {
                "category": category,
                "children": [],
            }
            for category in categories
        }

        roots: list[dict] = []

        for category in categories:
            node = nodes[category.id]

            if category.parent_id is None:
                roots.append(node)
                continue

            parent = nodes.get(category.parent_id)
            if parent is not None:
                parent["children"].append(node)
            else:
                roots.append(node)

        return roots
