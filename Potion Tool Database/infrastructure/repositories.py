"""
Repositories concrets (JSON/JS) pour ingrédients, recettes et data.js.

- JsonIngredientRepo : ingredients.json
- JsonRecipeRepo     : recipes.json
- JsDataRepo         : data.js (ORIGIN_TREE + BOOKS)
"""

from __future__ import annotations

import threading
from typing import Iterable, List, Optional

from domain.models import Ingredient, Recipe
from domain.errors import RepositoryError, NotFoundError, DuplicateNameError
from adapters.mapping import (
    ingredient_to_dto, ingredient_from_dto,
    recipe_to_dto, recipe_from_dto,
    ensure_origin_tree, ensure_books_list,
)
from .io_json import read_json_file, write_json_file
from .io_jsdata import read_data_js, write_data_js


# ---------- Base thread-safe mixin ----------

class _LockingRepo:
    def __init__(self) -> None:
        self._lock = threading.RLock()

    def _locked(self):
        return self._lock


# ---------- Ingredients ----------

class JsonIngredientRepo(_LockingRepo):
    def __init__(self, path: str) -> None:
        super().__init__()
        self.path = path

    # --- API publique ---

    def list_all(self) -> List[Ingredient]:
        with self._locked():
            dtos = read_json_file(self.path, expect_list=True)
            return [ingredient_from_dto(d) for d in dtos]

    def get_by_name(self, name: str) -> Ingredient:
        with self._locked():
            for ing in self.list_all():
                if ing.name == name:
                    return ing
            raise NotFoundError(f"Ingrédient introuvable: {name!r}")

    def add(self, ing: Ingredient) -> None:
        with self._locked():
            items = self.list_all()
            if any(i.name == ing.name for i in items):
                raise DuplicateNameError(f"Ingrédient déjà existant: {ing.name!r}")
            items.append(ing)
            self._save(items)

    def update(self, ing: Ingredient) -> None:
        with self._locked():
            items = self.list_all()
            idx = next((i for i, it in enumerate(items) if it.name == ing.name), -1)
            if idx < 0:
                raise NotFoundError(f"Ingrédient introuvable: {ing.name!r}")
            items[idx] = ing
            self._save(items)

    def delete(self, name: str) -> None:
        with self._locked():
            items = self.list_all()
            new_items = [i for i in items if i.name != name]
            if len(new_items) == len(items):
                # idempotent
                return
            self._save(new_items)

    # --- Internes ---

    def _save(self, items: Iterable[Ingredient]) -> None:
        dtos = [ingredient_to_dto(i) for i in items]
        write_json_file(self.path, dtos)


# ---------- Recipes ----------

class JsonRecipeRepo(_LockingRepo):
    def __init__(self, path: str) -> None:
        super().__init__()
        self.path = path

    def list_all(self) -> List[Recipe]:
        with self._locked():
            dtos = read_json_file(self.path, expect_list=True)
            return [recipe_from_dto(d) for d in dtos]

    def get_by_name(self, name: str) -> Recipe:
        with self._locked():
            for rec in self.list_all():
                if rec.name == name:
                    return rec
            raise NotFoundError(f"Recette introuvable: {name!r}")

    def add(self, recipe: Recipe) -> None:
        with self._locked():
            items = self.list_all()
            if any(r.name == recipe.name for r in items):
                raise DuplicateNameError(f"Recette déjà existante: {recipe.name!r}")
            items.append(recipe)
            self._save(items)

    def update(self, recipe: Recipe) -> None:
        with self._locked():
            items = self.list_all()
            idx = next((i for i, it in enumerate(items) if it.name == recipe.name), -1)
            if idx < 0:
                raise NotFoundError(f"Recette introuvable: {recipe.name!r}")
            items[idx] = recipe
            self._save(items)

    def delete(self, name: str) -> None:
        with self._locked():
            items = self.list_all()
            new_items = [r for r in items if r.name != name]
            if len(new_items) == len(items):
                return
            self._save(new_items)

    def _save(self, items: Iterable[Recipe]) -> None:
        dtos = [recipe_to_dto(r) for r in items]
        write_json_file(self.path, dtos)


# ---------- Data.js (ORIGIN_TREE + BOOKS) ----------

class JsDataRepo(_LockingRepo):
    """
    Repository pour le fichier data.js.

    Lecture prudente (parser littéraux), écriture en format ES module:
    export const ORIGIN_TREE = {...};
    export const BOOKS = [...];
    """

    def __init__(self, path: str) -> None:
        super().__init__()
        self.path = path

    # --- livres ---

    def get_books(self) -> List[str]:
        with self._locked():
            origin_tree, books = read_data_js(self.path)
            return ensure_books_list(books)

    def set_books(self, books: List[str]) -> None:
        with self._locked():
            origin_tree, _ = read_data_js(self.path)
            write_data_js(self.path, origin_tree=ensure_origin_tree(origin_tree), books=ensure_books_list(books))

    # --- origines ---

    def get_origin_tree(self) -> dict:
        with self._locked():
            origin_tree, books = read_data_js(self.path)
            return ensure_origin_tree(origin_tree)

    def set_origin_tree(self, tree: dict) -> None:
        with self._locked():
            _, books = read_data_js(self.path)
            write_data_js(self.path, origin_tree=ensure_origin_tree(tree), books=ensure_books_list(books))
