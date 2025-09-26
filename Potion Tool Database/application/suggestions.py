"""
SuggestionsService : utilitaires non-critiques pour assister la saisie
(auto-complétion d'alternatives, tri par difficulté, presets).
"""

from __future__ import annotations

from typing import Iterable, List, Optional, Sequence, Tuple

from domain.models import Ingredient
from domain.value_objects import Category


class SuggestionsService:
    def __init__(self, ingredients_repo) -> None:
        self.ingredients_repo = ingredients_repo

    # ---------------------------
    # Sélections par catégorie
    # ---------------------------

    def list_by_category(self, category: str) -> List[Ingredient]:
        cat = Category.normalize(category)
        return sorted(
            [i for i in self.ingredients_repo.list_all() if i.cat == cat],
            key=lambda ing: (ing.difficulty, ing.name.lower()),
        )

    # ---------------------------
    # Compléter une alternative
    # ---------------------------

    def suggest_combo_completion(
        self,
        *,
        liant: Optional[str] = None,
        catalyseur: Optional[str] = None,
        reactif: Optional[str] = None,
        prefer_low_difficulty: bool = True,
        restrict_books: Optional[Sequence[str]] = None,
        restrict_origins: Optional[Sequence[str]] = None,
    ) -> Tuple[str, str, str]:
        """
        Propose un trio (liant, catalyseur, reactif) cohérent.
        - si un ou plusieurs sont déjà fournis, on complète les manquants
        - stratégie par défaut : prend la difficulté la plus basse compatible
        - restrictions possibles : livres et origines
        """
        restrict_books = list(restrict_books or [])
        restrict_origins = list(restrict_origins or [])

        def _match(ing: Ingredient, wanted_cat: str) -> bool:
            if ing.cat != wanted_cat:
                return False
            if restrict_books and not any(b in ing.books for b in restrict_books):
                return False
            if restrict_origins and not any(o in ing.origins for o in restrict_origins):
                return False
            return True

        li = liant
        ca = catalyseur
        re = reactif

        # pickers
        if not li:
            li_candidates = [i for i in self.ingredients_repo.list_all() if _match(i, Category.LIANT.value)]
            li = _pick(li_candidates, prefer_low_difficulty)
        if not ca:
            ca_candidates = [i for i in self.ingredients_repo.list_all() if _match(i, Category.CATALYSEUR.value)]
            ca = _pick(ca_candidates, prefer_low_difficulty)
        if not re:
            re_candidates = [i for i in self.ingredients_repo.list_all() if _match(i, Category.REACTIF.value)]
            re = _pick(re_candidates, prefer_low_difficulty)

        return (li or "", ca or "", re or "")


# --- internals ---

def _pick(candidates: List[Ingredient], prefer_low_diff: bool) -> Optional[str]:
    if not candidates:
        return None
    if prefer_low_diff:
        candidates = sorted(candidates, key=lambda ing: (ing.difficulty, ing.name.lower()))
    else:
        candidates = sorted(candidates, key=lambda ing: (-ing.difficulty, ing.name.lower()))
    return candidates[0].name
