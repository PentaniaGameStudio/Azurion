"""
Use cases (Application layer) pour Potion DB Tool.
Orchestration de la logique métier + validation + accès aux dépôts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from domain.models import Ingredient, Recipe
from domain.value_objects import Category
from domain.errors import (
    NotFoundError,
    DuplicateNameError,
    ValidationError,
)
from application.validators import ValidationService


# ---------------------------
# Helpers génériques
# ---------------------------

def _find_by_name(items: Iterable, name: str):
    for x in items:
        # objets domaine (dataclasses)
        if getattr(x, "name", None) == name:
            return x
        # DTO éventuel (sécurité)
        if isinstance(x, dict) and x.get("name") == name:
            return x
    return None


def _generate_copy_name(base: str, existing: set[str]) -> str:
    """
    Produit un nom unique à partir de base.
    Stratégie: "base (copie)" puis "base (copie 2)", "base (copie 3)", ...
    """
    if base not in existing:
        return base
    n = 2
    candidate = f"{base} (copie)"
    if candidate not in existing:
        return candidate
    while True:
        candidate = f"{base} (copie {n})"
        if candidate not in existing:
            return candidate
        n += 1


# ---------------------------
# INGREDIENTS
# ---------------------------

@dataclass
class CreateIngredient:
    repo: any
    validator: ValidationService

    def __init__(self, repo, validator: ValidationService) -> None:
        self.repo = repo
        self.validator = validator

    def execute(self, *, name: str, cat: str, difficulty: int,
                shortEffect: Optional[str], effect: Optional[str],
                books: list[str], origins: list[str]) -> None:
        category = Category.normalize(cat)
        ing = Ingredient(
            name=name.strip(),
            cat=category,
            difficulty=int(difficulty or 0),
            short_effect=(shortEffect or "").strip() or None,
            effect=(effect or "").strip() or None,
            origins=list(origins),  # <-- normalisées en chemins complets
            books=list(books or []),
        )
        self.validator.validate_ingredient(ing, check_unique=True)
        self.repo.add(ing)


@dataclass
class UpdateIngredient:
    repo: any
    validator: ValidationService

    def __init__(self, repo, validator: ValidationService) -> None:
        self.repo = repo
        self.validator = validator

    def execute(self, *, name: str, cat: str, difficulty: int,
                shortEffect: Optional[str], effect: Optional[str],
                books: list[str], origins: list[str]) -> None:
        category = Category.normalize(cat)
        ing = Ingredient(
            name=name.strip(),
            cat=category,
            difficulty=int(difficulty or 0),
            short_effect=(shortEffect or "").strip() or None,
            effect=(effect or "").strip() or None,
            origins=list(origins or []),
            books=list(books or []),
        )
        self.validator.validate_ingredient(ing, check_unique=False)
        if _find_by_name(self.repo.list_all(), ing.name) is None:
            raise NotFoundError(f"Ingrédient introuvable: {ing.name!r}")
        self.repo.update(ing)


@dataclass
class DeleteIngredient:
    repo: any
    validator: ValidationService

    def __init__(self, repo, validator: ValidationService) -> None:
        self.repo = repo
        self.validator = validator

    def execute(self, name: str) -> None:
        if not name:
            raise ValidationError("Nom d'ingrédient vide.")
        if _find_by_name(self.repo.list_all(), name) is None:
            raise NotFoundError(f"Ingrédient introuvable: {name!r}")
        self.repo.delete(name)


@dataclass
class DuplicateIngredient:
    repo: any
    validator: ValidationService

    def __init__(self, repo, validator: ValidationService) -> None:
        self.repo = repo
        self.validator = validator

    def execute(self, source_name: str) -> str:
        src = _find_by_name(self.repo.list_all(), source_name)
        if src is None:
            raise NotFoundError(f"Ingrédient introuvable: {source_name!r}")

        # Les repos retournent des objets domaine -> on lit directement les attributs
        names = {i.name for i in self.repo.list_all()}
        new_name = _generate_copy_name(f"{source_name}", names)

        clone = Ingredient(
            name=new_name,
            cat=getattr(src, "cat", src["cat"] if isinstance(src, dict) else ""),
            difficulty=int(getattr(src, "difficulty", src.get("difficulty", 0) if isinstance(src, dict) else 0) or 0),
            short_effect=getattr(src, "short_effect", src.get("shortEffect") if isinstance(src, dict) else None),
            effect=getattr(src, "effect", src.get("effect") if isinstance(src, dict) else None),
            origins=list(getattr(src, "origins", src.get("origins", []) if isinstance(src, dict) else []) or []),
            books=list(getattr(src, "books", src.get("books", []) if isinstance(src, dict) else []) or []),
        )
        self.validator.validate_ingredient(clone, check_unique=True)
        self.repo.add(clone)
        return new_name


# ---------------------------
# RECIPES
# ---------------------------

@dataclass
class CreateRecipe:
    repo: any
    ingredients_repo: any
    validator: ValidationService

    def __init__(self, repo, ingredients_repo, validator: ValidationService) -> None:
        self.repo = repo
        self.ingredients_repo = ingredients_repo
        self.validator = validator

    def execute(self, *, name: str, desc: str, emoji: Optional[str], bonus: Optional[float],
                combos: list[list[str]], books: Optional[list[str]] = None) -> None:
        recipe = Recipe(
            name=name.strip(),
            desc=desc.strip(),
            emoji=(emoji or "").strip() or None,
            bonus=float(bonus) if bonus not in (None, "") else None,
            combos=[list(c) for c in (combos or [])],
            books=list(books or []),  # NEW
        )
        self.validator.validate_recipe(recipe, check_unique=True)
        # ✅ persiste la création
        self.repo.add(recipe)


@dataclass
class UpdateRecipe:
    repo: any
    ingredients_repo: any
    validator: ValidationService

    def __init__(self, repo, ingredients_repo, validator: ValidationService) -> None:
        self.repo = repo
        self.ingredients_repo = ingredients_repo
        self.validator = validator

    def execute(self, *, name: str, desc: str, emoji: Optional[str], bonus: Optional[float],
                combos: list[list[str]], books: Optional[list[str]] = None) -> None:
        recipe = Recipe(
            name=name.strip(),
            desc=desc.strip(),
            emoji=(emoji or "").strip() or None,
            bonus=float(bonus) if bonus not in (None, "") else None,
            combos=[list(c) for c in (combos or [])],
            books=list(books or []),  # NEW
        )
        self.validator.validate_recipe(recipe, check_unique=False)
        if _find_by_name(self.repo.list_all(), recipe.name) is None:
            raise NotFoundError(f"Recette introuvable: {recipe.name!r}")
        self.repo.update(recipe)


@dataclass
class DeleteRecipe:
    repo: any
    validator: ValidationService

    def __init__(self, repo, validator: ValidationService) -> None:
        self.repo = repo
        self.validator = validator

    def execute(self, name: str) -> None:
        if not name:
            raise ValidationError("Nom de recette vide.")
        if _find_by_name(self.repo.list_all(), name) is None:
            raise NotFoundError(f"Recette introuvable: {name!r}")
        self.repo.delete(name)


@dataclass
class DuplicateRecipe:
    repo: any
    validator: ValidationService

    def __init__(self, repo, validator: ValidationService) -> None:
        self.repo = repo
        self.validator = validator

    def execute(self, source_name: str) -> str:
        src = _find_by_name(self.repo.list_all(), source_name)
        if src is None:
            raise NotFoundError(f"Recette introuvable: {source_name!r}")

        names = {r.name for r in self.repo.list_all()}
        new_name = _generate_copy_name(f"{source_name}", names)

        # Objets domaine -> lecture directe
        src_combos = getattr(src, "combos", None)
        if src_combos is None and isinstance(src, dict):
            src_combos = list(src.get("ingredients", []) or [])
        combos = [list(c) for c in (src_combos or [])]

        clone = Recipe(
            name=new_name,
            desc=getattr(src, "desc", src.get("desc") if isinstance(src, dict) else None),
            emoji=getattr(src, "emoji", src.get("emoji") if isinstance(src, dict) else None),
            bonus=getattr(src, "bonus", src.get("bonus") if isinstance(src, dict) else None),
            combos=combos,
            books=list(getattr(src, "books", src.get("books") if isinstance(src, dict) else []) or []),  # NEW
        )
        self.validator.validate_recipe(clone, check_unique=True)
        self.repo.add(clone)
        return new_name


# ---------------------------
# BOOKS
# ---------------------------

@dataclass
class AddBook:
    data_repo: any
    validator: ValidationService

    def __init__(self, data_repo, validator: ValidationService) -> None:
        self.data_repo = data_repo
        self.validator = validator

    def execute(self, title: str) -> None:
        t = (title or "").strip()
        if not t:
            raise ValidationError("Titre de livre vide.")
        books = list(self.data_repo.get_books())
        if t in books:
            raise DuplicateNameError(f"Livre déjà existant: {t!r}")
        books.append(t)
        books = sorted(set(books))
        self.data_repo.set_books(books)


@dataclass
class RenameBook:
    data_repo: any
    validator: ValidationService

    def __init__(self, data_repo, validator: ValidationService) -> None:
        self.data_repo = data_repo
        self.validator = validator

    def execute(self, old_title: str, new_title: str) -> None:
        old_t = (old_title or "").strip()
        new_t = (new_title or "").strip()
        if not old_t or not new_t:
            raise ValidationError("Titre de livre vide.")
        books = list(self.data_repo.get_books())
        if old_t not in books:
            raise NotFoundError(f"Livre introuvable: {old_t!r}")
        if new_t != old_t and new_t in books:
            raise DuplicateNameError(f"Livre déjà existant: {new_t!r}")
        # Remplacement simple
        books = [new_t if b == old_t else b for b in books]
        self.data_repo.set_books(books)


@dataclass
class RemoveBook:
    data_repo: any
    ingredients_repo: any
    validator: ValidationService

    def __init__(self, data_repo, validator: ValidationService) -> None:
        self.data_repo = data_repo
        self.validator = validator

    def execute(self, title: str) -> None:
        t = (title or "").strip()
        if not t:
            raise ValidationError("Titre de livre vide.")
        books = list(self.data_repo.get_books())
        if t not in books:
            # idempotent
            return
        books = [b for b in books if b != t]
        self.data_repo.set_books(books)
        # Défensif : supprimer les références restantes dans les ingrédients (si l'UI n'a pas migré)
        try:
            ingredients_repo = getattr(self, "ingredients_repo", None) or self.validator.ingredients_repo
            for ing in list(ingredients_repo.list_all()):
                if t in ing.books:
                    ing.books = [b for b in ing.books if b != t]
                    ingredients_repo.update(ing)
        except Exception:
            pass


@dataclass
class MigrateBookRefs:
    data_repo: any
    ingredients_repo: any
    recipes_repo: any
    validator: ValidationService

    def __init__(self, data_repo, ingredients_repo, recipes_repo, validator: ValidationService) -> None:
        self.data_repo = data_repo
        self.ingredients_repo = ingredients_repo
        self.recipes_repo = recipes_repo
        self.validator = validator

    def execute(self, *, old_title: str, new_title: str) -> None:
        old_t = (old_title or "").strip()
        new_t = (new_title or "").strip()
        if not old_t:
            raise ValidationError("Ancien titre vide.")
        # new_t peut être == old_t ; ou un livre qui vient d’être ajouté
        for ing in list(self.ingredients_repo.list_all()):
            if old_t in ing.books:
                new_books = [new_t if b == old_t else b for b in ing.books if (new_t or (b != old_t))]
                ing.books = list(dict.fromkeys(new_books))  # unique
                self.ingredients_repo.update(ing)


# ---------------------------
# ORIGINS
# ---------------------------

@dataclass
class AddOrigin:
    data_repo: any
    validator: ValidationService

    def __init__(self, data_repo, validator: ValidationService) -> None:
        self.data_repo = data_repo
        self.validator = validator

    def execute(self, parent_path: str, new_name: str) -> None:
        tree = self.data_repo.get_origin_tree()
        parent = _get_node_by_path(tree, parent_path)
        if parent is None or not isinstance(parent, dict):
            raise NotFoundError(f"Nœud parent introuvable: {parent_path!r}")
        name = (new_name or "").strip()
        if not name:
            raise ValidationError("Nom du nœud vide.")
        if name in parent:
            raise DuplicateNameError(f"Nœud déjà existant sous {parent_path!r}: {name!r}")
        parent[name] = {}
        self.data_repo.set_origin_tree(tree)


@dataclass
class RenameOrigin:
    data_repo: any
    validator: ValidationService

    def __init__(self, data_repo, validator: ValidationService) -> None:
        self.data_repo = data_repo
        self.validator = validator

    def execute(self, old_path: str, new_name: str) -> None:
        tree = self.data_repo.get_origin_tree()
        parent_path, last = _split_path(old_path)
        parent = _get_node_by_path(tree, parent_path)
        if parent is None or not isinstance(parent, dict) or last not in parent:
            raise NotFoundError(f"Nœud introuvable: {old_path!r}")
        nn = (new_name or "").strip()
        if not nn:
            raise ValidationError("Nouveau nom vide.")
        if nn in parent and nn != last:
            raise DuplicateNameError(f"Nœud déjà existant: {nn!r}")
        parent[nn] = parent.pop(last)
        self.data_repo.set_origin_tree(tree)


@dataclass
class RemoveOrigin:
    data_repo: any
    validator: ValidationService

    def __init__(self, data_repo, validator: ValidationService) -> None:
        self.data_repo = data_repo
        self.validator = validator

    def execute(self, path: str) -> None:
        tree = self.data_repo.get_origin_tree()
        parent_path, last = _split_path(path)
        parent = _get_node_by_path(tree, parent_path)
        if parent is None or not isinstance(parent, dict) or last not in parent:
            # idempotent
            return
        del parent[last]
        self.data_repo.set_origin_tree(tree)


@dataclass
class MigrateOriginRefs:
    data_repo: any
    ingredients_repo: any
    recipes_repo: any
    validator: ValidationService

    def __init__(self, data_repo, ingredients_repo, recipes_repo, validator: ValidationService) -> None:
        self.data_repo = data_repo
        self.ingredients_repo = ingredients_repo
        self.recipes_repo = recipes_repo
        self.validator = validator

    def execute(self, *, old_path: str, new_name: str) -> None:
            """
            Migration par LIBELLÉ (stockage base = libellés, pas chemins).
            old_path: libellé source (dernier segment si on reçoit un chemin)
            new_name: libellé cible ("" => suppression)
            """
            old_label = (old_path or "").split("/")[-1].strip()
            new_label = (new_name or "").split("/")[-1].strip()
            if not old_label:
                raise ValidationError("Ancienne origine vide.")

            for ing in list(self.ingredients_repo.list_all()):
                if old_label in (ing.origins or []):
                    if new_label:
                        ing.origins = list(dict.fromkeys([(new_label if o == old_label else o) for o in ing.origins]))
                    else:
                        ing.origins = [o for o in ing.origins if o != old_label]
                    self.ingredients_repo.update(ing)


# ---------------------------
# DATASET
# ---------------------------

@dataclass
class ValidateDataset:
    validator: ValidationService

    def __init__(self, validator: ValidationService) -> None:
        self.validator = validator

    def execute(self) -> None:
        """
        Valide tout le dataset ou lève ValidationError détaillée au premier problème détecté.
        """
        # ingrédients
        seen_ing = set()
        for ing in self.validator.ingredients_repo.list_all():
            self.validator.validate_ingredient(ing, check_unique=False)
            if ing.name in seen_ing:
                raise DuplicateNameError(f"Doublon d'ingrédient: {ing.name!r}")
            seen_ing.add(ing.name)

        # recettes
        seen_rec = set()
        for r in self.validator.recipes_repo.list_all():
            self.validator.validate_recipe(r, check_unique=False)
            if r.name in seen_rec:
                raise DuplicateNameError(f"Doublon de recette: {r.name!r}")
            seen_rec.add(r.name)


@dataclass
class InspectDataset:
    integrity: any  # IntegrityService

    def __init__(self, integrity) -> None:
        self.integrity = integrity

    def execute(self):
        """
        Retourne un rapport d'inspection (dataclass InspectionReport).
        """
        return self.integrity.inspect()


# ---------------------------
# Utilitaires pour l'arbre
# ---------------------------

def _split_path(path: str) -> tuple[str, str]:
    parts = [p for p in (path or "").split("/") if p]
    if not parts:
        return "", ""
    parent = "/".join(parts[:-1])
    last = parts[-1]
    return parent, last


def _get_node_by_path(tree: dict, path: str) -> Optional[dict]:
    if path in ("", None):
        return tree
    node = tree
    for part in [p for p in path.split("/") if p]:
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node if isinstance(node, dict) else None
