"""
Value Objects & énumérations.
"""

from __future__ import annotations

from enum import Enum
from typing import NewType


class Category(Enum):
    LIANT = "Liant"
    CATALYSEUR = "Catalyseur"
    REACTIF = "Réactif"

    @classmethod
    def normalize(cls, value: str) -> str:
        """
        Normalise une chaîne arbitraire vers les 3 libellés officiels.
        Tolère la casse et quelques alias usuels.
        """
        if value is None:
            raise ValueError("Catégorie manquante.")
        v = str(value).strip().lower()
        if v in {"liant", "binder"}:
            return cls.LIANT.value
        if v in {"catalyseur", "catalyst", "cata"}:
            return cls.CATALYSEUR.value
        if v in {"réactif", "reactif", "reactant"}:
            return cls.REACTIF.value
        # si déjà conforme
        if value in {c.value for c in cls}:
            return value
        raise ValueError(f"Catégorie inconnue: {value!r}")


# Typages nominaux (documentation + static typing)
BookTitle = NewType("BookTitle", str)
OriginPath = NewType("OriginPath", str)
IngredientName = NewType("IngredientName", str)
RecipeName = NewType("RecipeName", str)
