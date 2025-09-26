"""
IntegrityService : produit un rapport d'inspection transversal du dataset.
- livres manquants (référencés par ingrédients mais absents du référentiel)
- origines invalides (non-feuilles ou absentes)
- ingrédients non utilisés par des recettes
- recettes invalides (références cassées ou combos incorrects)
- doublons de noms (ingrédients/recettes)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Set

from domain.errors import NotFoundError, RecipeError
from domain import rules


@dataclass(frozen=True)
class InspectionReport:
    missing_books: List[str]
    invalid_origins: List[str]
    unused_ingredients: List[str]
    invalid_recipes: List[str]
    duplicate_names: List[str]


class IntegrityService:
    def __init__(self, ingredients_repo, recipes_repo, data_repo) -> None:
        self.ingredients_repo = ingredients_repo
        self.recipes_repo = recipes_repo
        self.data_repo = data_repo

    def inspect(self) -> InspectionReport:
        ings = list(self.ingredients_repo.list_all())
        recs = list(self.recipes_repo.list_all())
        books_ref = set(self.data_repo.get_books() or [])

        # Prépare référentiels d'origines
        nodes = set(_list_all_nodes(self.data_repo.get_origin_tree()))  # chemins complets
        labels = {n.split("/")[-1] for n in nodes}                      # libellés uniques

        # ---- Livres manquants ----
        referenced_books: Set[str] = set()
        for ing in ings:
            for b in (ing.books or []):
                if b:
                    referenced_books.add(b)
        missing_books = sorted(list(referenced_books - books_ref))

        # ---- Origines invalides (on s'attend à des libellés en base) ----
        referenced_origins: Set[str] = set()
        for ing in ings:
            for o in (ing.origins or []):
                if o:
                    referenced_origins.add(o)

        invalid_origins = sorted([
            o for o in referenced_origins
            if not (
                o in labels   # libellé valide
                or o in nodes # tolérance: si quelqu'un a stocké un chemin complet
            )
        ])

        # ---- Ingrédients non utilisés ----
        used_ing: Set[str] = set()
        for r in recs:
            combos = getattr(r, "combos", None)
            if combos is None:
                combos = getattr(r, "ingredients", [])  # tolérance DTO
            for c in combos or []:
                for name in (list(c) if isinstance(c, (list, tuple)) else []):
                    if name:
                        used_ing.add(name)
        unused_ingredients = sorted([i.name for i in ings if i.name not in used_ing])

        # ---- Recettes invalides (utilise la règle assouplie) ----
        invalid_recipes: Set[str] = set()
        for r in recs:
            combos = getattr(r, "combos", None)
            if combos is None:
                combos = getattr(r, "ingredients", [])
            for c in combos or []:
                try:
                    rules.validate_combo(c, self.ingredients_repo)
                except (NotFoundError, RecipeError):
                    invalid_recipes.add(r.name)
                    break

        # ---- Doublons ----
        dup_ing = rules.find_duplicates([i.name for i in ings])
        dup_rec = rules.find_duplicates([r.name for r in recs])
        duplicate_names = sorted(list(set(dup_ing) | set(dup_rec)))

        return InspectionReport(
            missing_books=missing_books,
            invalid_origins=invalid_origins,
            unused_ingredients=unused_ingredients,
            invalid_recipes=sorted(list(invalid_recipes)),
            duplicate_names=duplicate_names,
        )


# --- Utils ---

def _list_all_nodes(node: dict, prefix: str = "") -> List[str]:
    out: List[str] = []
    for label, children in (node or {}).items():
        key = f"{prefix}/{label}" if prefix else label
        out.append(key)
        if isinstance(children, dict) and children:
            out.extend(_list_all_nodes(children, key))
    return out
