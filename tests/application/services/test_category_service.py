from uuid import uuid4

from app.application.services.category_service import CategoryService
from app.domain.entities.knowledge_category import KnowledgeCategory


class InMemoryCategoryRepository:
    def __init__(self, categories=None):
        self.categories = list(categories or [])

    def save(self, category):
        self.categories.append(category)

    def get_by_id(self, category_id):
        return next(
            (
                category
                for category in self.categories
                if category.id == category_id
            ),
            None,
        )

    def get_all(self):
        return list(self.categories)


def test_get_categories_returns_repository_categories():
    root = KnowledgeCategory(
        id=uuid4(),
        name="Meaning",
    )
    child = KnowledgeCategory(
        id=uuid4(),
        name="Lexical Meaning",
        parent_id=root.id,
    )

    repository = InMemoryCategoryRepository([root, child])
    service = CategoryService(repository)

    assert service.get_categories() == [root, child]


def test_get_category_tree_builds_parent_child_relationships():
    root = KnowledgeCategory(
        id=uuid4(),
        name="Meaning",
    )
    child = KnowledgeCategory(
        id=uuid4(),
        name="Lexical Meaning",
        parent_id=root.id,
    )
    grandchild = KnowledgeCategory(
        id=uuid4(),
        name="Translation",
        parent_id=child.id,
    )

    repository = InMemoryCategoryRepository(
        [root, child, grandchild]
    )
    service = CategoryService(repository)

    tree = service.get_category_tree()

    assert tree == [
        {
            "category": root,
            "children": [
                {
                    "category": child,
                    "children": [
                        {
                            "category": grandchild,
                            "children": [],
                        }
                    ],
                }
            ],
        }
    ]


def test_get_category_tree_keeps_orphan_categories_as_roots():
    missing_parent_id = uuid4()

    orphan = KnowledgeCategory(
        id=uuid4(),
        name="Orphan",
        parent_id=missing_parent_id,
    )

    repository = InMemoryCategoryRepository([orphan])
    service = CategoryService(repository)

    tree = service.get_category_tree()

    assert tree == [
        {
            "category": orphan,
            "children": [],
        }
    ]
