"""
ValidationService : règles de validation de haut niveau pour ingrédients/recettes,
adossées aux repositories et aux règles métier.
"""

from __future__ import annotations

from typing import Iterable, List, Optional, Sequence

from domain.models import Ingredient, Recipe
from domain.value_objects import Category
from domain.errors import (
    ValidationError,
    DuplicateNameError,
    CategoryError,
    OriginError,
    BookError,
    RecipeError,
    NotFoundError,
)
from domain import rules


class ValidationService:
    """
    Service de validation centralisé. Ne fait pas d'I/O direct (les repos sont injectés).
    """

    def __init__(self, ingredients_repo, recipes_repo, data_repo) -> None:
        self.ingredients_repo = ingredients_repo
        self.recipes_repo = recipes_repo
        self.data_repo = data_repo


    # --------- Ingrédient ---------

    def validate_ingredient(self, ing: Ingredient, *, check_unique: bool) -> None:
        # Nom
        if not ing.name:
            raise ValidationError("Le nom de l'ingrédient est obligatoire.")

        if check_unique:
            if any(i.name == ing.name for i in self.ingredients_repo.list_all()):
                raise DuplicateNameError(f"Ingrédient déjà existant: {ing.name!r}")

        # Catégorie
        try:
            Category.normalize(ing.cat)
        except Exception as e:
            raise CategoryError(str(e))

        # Difficulty : tout entier (négatif autorisé)
        try:
            int(ing.difficulty)
        except Exception:
            raise ValidationError("La difficulté doit être un entier (positif, nul ou négatif).")

        # Livres
        self._ensure_books_exist(ing.books)

        # Origines :
        #  1) normaliser en LIBELLÉS (dernier segment)
        #  2) valider que chaque libellé existe quelque part dans l'arbre
        ing.origins = self.normalize_origins(ing.origins)
        self._ensure_origin_labels_exist(ing.origins)


    # --------- Recette ---------
    def validate_recipe(self, recipe, *, check_unique: bool) -> None:
        # Nom obligatoire
        if not recipe.name:
            raise ValidationError("Le nom de la recette est obligatoire.")

        # Unicité optionnelle
        if check_unique:
            if any(r.name == recipe.name for r in self.recipes_repo.list_all()):
                raise DuplicateNameError(f"Recette déjà existante: {recipe.name!r}")

        # Combos = [][] d'ingrédients
        combos = recipe.combos
        if combos is None:
            combos = []
        if not isinstance(combos, list):
            raise RecipeError("Le champ 'ingredients' doit être une liste d'alternatives (liste).")

        # ///summary: normaliser les combos -> liste de listes de chaînes non vides
        norm = []
        for row in combos:
            if not isinstance(row, (list, tuple)):
                raise RecipeError("Chaque alternative doit être une liste.")
            cleaned = []
            for x in row:
                s = "" if x is None else str(x).strip()
                if s:
                    cleaned.append(s)
            if cleaned:
                norm.append(cleaned)
        if not norm:
            raise RecipeError("Au moins une alternative non vide est requise.")
        recipe.combos = norm  # on remplace par la version nettoyée

        # ///summary: NEW — valider/normaliser les livres à partir de recipe.books (et non 'dto')
        books_raw = getattr(recipe, "books", [])
        books = _normalize_books_list(books_raw)
        known_books = set(self.data_repo.get_books() or [])
        unknown = [b for b in books if b not in known_books]
        if unknown:
            raise BookError(f"Unknown book(s) in recipe: {', '.join(unknown)}")
        recipe.books = books  # on remplace par la version normalisée


    # --------- Origines / Livres helpers ---------

    def list_origin_nodes(self) -> List[str]:
        tree = self.data_repo.get_origin_tree()
        return _list_all_nodes(tree)

    def list_origin_labels(self) -> List[str]:
        tree = self.data_repo.get_origin_tree()
        return _list_labels(tree)

    def _ensure_origin_labels_exist(self, origins: Sequence[str]) -> None:
        """Chaque élément de `origins` doit être un libellé existant dans l'arbre."""
        labels = set(self.list_origin_labels())
        for o in origins or []:
            if not o:
                # on ignore les vides déjà nettoyés en amont, mais si tu préfères: raise ValidationError
                continue
            if o not in labels:
                raise OriginError(f"Origine inconnue (libellé): {o!r}")

    def _ensure_books_exist(self, books: Sequence[str]) -> None:
        ref = set(self.data_repo.get_books() or [])
        for b in books or []:
            if b not in ref:
                raise BookError(f"Livre inconnu: {b!r}")

    def normalize_origin(self, origin: str) -> str:
        """Accepte un libellé ou un chemin, RENVOIE TOUJOURS le libellé (dernier segment) s'il existe."""
        if not origin:
            raise OriginError("Origine vide.")
        label = origin.split("/")[-1].strip()
        if not label:
            raise OriginError("Origine vide.")
        if label in set(self.list_origin_labels()):
            return label
        raise OriginError(f"Origine inconnue: {origin!r}")

    def normalize_origins(self, origins) -> list[str]:
        # Unique en conservant l'ordre
        seen = set()
        out: list[str] = []
        for o in (origins or []):
            try:
                lab = self.normalize_origin(o)
            except OriginError:
                # on propage l'erreur de la 1re origine invalide
                raise
            if lab not in seen:
                seen.add(lab)
                out.append(lab)
        return out


# --------- Helper local manquant (ajouté) ---------

def _list_leaves(node: dict, prefix: str = "") -> List[str]:
    """
    Retourne toutes les feuilles de l'arbre {str: dict|{}} sous forme "path/..".
    """
    out: List[str] = []
    for label, children in (node or {}).items():
        key = f"{prefix}/{label}" if prefix else label
        if isinstance(children, dict) and children:
            out.extend(_list_leaves(children, key))
        else:
            out.append(key)
    return out

def _list_all_nodes(node: dict, prefix: str = "") -> List[str]:
    out: List[str] = []
    for label, children in (node or {}).items():
        key = f"{prefix}/{label}" if prefix else label
        out.append(key)
        if isinstance(children, dict) and children:
            out.extend(_list_all_nodes(children, key))
    return out

def _list_labels(node: dict) -> List[str]:
    """Tous les libellés (parents + feuilles), uniques triés."""
    out: List[str] = []
    def walk(n: dict):
        for k, v in (n or {}).items():
            out.append(str(k))
            if isinstance(v, dict) and v:
                walk(v)
    walk(node or {})
    return sorted(set(out))

def _normalize_books_list(books: Optional[List[str]]) -> List[str]:
    if not books:
        return []
    out = []
    seen = set()
    for b in books:
        if not isinstance(b, str):
            continue
        t = b.strip()
        if not t or t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out
