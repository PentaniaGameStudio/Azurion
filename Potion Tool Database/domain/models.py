"""
Domain models pour Potion DB Tool.
Ne dépend d'aucun framework UI ni des repositories concrets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(slots=True)
class Ingredient:
    """
    Entité de base : un ingrédient d'alchimie.
    - name : identifiant logique (unique)
    - cat  : 'Liant' | 'Catalyseur' | 'Réactif'
    """
    name: str
    cat: str
    difficulty: int = 0
    short_effect: Optional[str] = None
    effect: Optional[str] = None
    origins: List[str] = field(default_factory=list)
    books: List[str] = field(default_factory=list)

    # Petites commodités domain (immutables simples, pas d'IO ici)
    def with_name(self, new_name: str) -> "Ingredient":
        return Ingredient(
            name=new_name,
            cat=self.cat,
            difficulty=self.difficulty,
            short_effect=self.short_effect,
            effect=self.effect,
            origins=list(self.origins),
            books=list(self.books),
        )

    def add_origin(self, origin_path: str) -> "Ingredient":
        if origin_path not in self.origins:
            new = list(self.origins)
            new.append(origin_path)
            self.origins = new
        return self

    def remove_origin(self, origin_path: str) -> "Ingredient":
        if origin_path in self.origins:
            new = [o for o in self.origins if o != origin_path]
            self.origins = new
        return self

    def add_book(self, title: str) -> "Ingredient":
        if title not in self.books:
            new = list(self.books)
            new.append(title)
            self.books = new
        return self

    def remove_book(self, title: str) -> "Ingredient":
        if title in self.books:
            new = [b for b in self.books if b != title]
            self.books = new
        return self


@dataclass(slots=True)
class Recipe:
    """
    Recette composée d'alternatives (combos) de 3 ingrédients (1/1/1).
    - combos : List[List[str]] ; chaque trio = [liant, catalyseur, reactif]
    """
    name: str
    desc: str
    emoji: Optional[str] = None
    bonus: Optional[float] = None
    books: List[str] = field(default_factory=list)
    combos: List[List[str]] = field(default_factory=list)

    def with_name(self, new_name: str) -> "Recipe":
        return Recipe(
            name=new_name,
            desc=self.desc,
            emoji=self.emoji,
            bonus=self.bonus,
            combos=[list(c) for c in self.combos],
            books=list(self.books),
        )
        
    def add_combo(self, liant: str, catalyseur: str, reactif: str) -> "Recipe":
        new = [list(c) for c in self.combos]
        new.append([liant, catalyseur, reactif])
        self.combos = new
        return self

    def remove_combo_at(self, index: int) -> "Recipe":
        if 0 <= index < len(self.combos):
            new = [list(c) for i, c in enumerate(self.combos) if i != index]
            self.combos = new
        return self
