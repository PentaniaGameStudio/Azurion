"""
Presenters (Domain/Repo -> ViewModels) pour l'UI.
Aucune dépendance à la GUI, uniquement des VMs (dataclasses).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, List, Optional


# ---------------------------
# Helpers (duck-typing gentle)
# ---------------------------

def _get(obj: Any, key: str, default: Any = None) -> Any:
    """Accède à un attribut ou une clé dict avec fallback."""
    if hasattr(obj, key):
        return getattr(obj, key)
    if isinstance(obj, dict) and key in obj:
        return obj[key]
    return default


# ---------------------------
# View Models
# ---------------------------

@dataclass(frozen=True)
class BookRowVM:
    title: str
    usage_count: int


@dataclass(frozen=True)
class BooksTableVM:
    rows: List[BookRowVM]


@dataclass(frozen=True)
class IngredientCardVM:
    name: str
    title: str
    category: str
    difficulty: int
    short_effect: Optional[str]
    effect: Optional[str]
    books: List[str]
    origins: List[str]               # -> libellés simples (mais on tolère des chemins côté lecture/filtre)


@dataclass(frozen=True)
class FilterSourcesVM:
    categories: List[str]
    books: List[str]
    origins: List[str]               # -> liste de libellés (tous les nœuds, parents + feuilles)


@dataclass(frozen=True)
class RecipeRowVM:
    name: str
    title: str
    emoji: Optional[str]
    bonus: Optional[float]
    books: List[str]
    combos: List[List[str]]          # alternatives de taille variable (>=1)


# ---------------------------
# Presenters
# ---------------------------

class BooksPresenter:
    """
    Présente la table des livres et leur taux d'usage (nb d'ingrédients les référencent).
    """

    def __init__(self, data_repo, ingredients_repo) -> None:
        self.data_repo = data_repo
        self.ingredients_repo = ingredients_repo

    def make_books_table(self) -> BooksTableVM:
        books: List[str] = list(self.data_repo.get_books())
        # Compter les usages par ingrédients
        usage = {b: 0 for b in books}
        for ing in self._list_ingredients():
            ing_books = _get(ing, "books", []) or []
            for b in ing_books:
                if b in usage:
                    usage[b] += 1
                else:
                    # livre référencé mais absent du référentiel -> on l'affiche aussi
                    usage.setdefault(b, 0)
                    usage[b] += 1
                    if b not in books:
                        books.append(b)

        rows = [BookRowVM(title=b, usage_count=usage.get(b, 0)) for b in sorted(books)]
        return BooksTableVM(rows=rows)

    def _list_ingredients(self) -> Iterable[Any]:
        # Le repo devra fournir list_all()
        return self.ingredients_repo.list_all()


class OriginsPresenter:
    """
    Présente l'arbre d'origines et expose des listes de feuilles.
    """

    def __init__(self, data_repo, ingredients_repo) -> None:
        self.data_repo = data_repo
        self.ingredients_repo = ingredients_repo

    def get_origin_tree(self) -> dict:
        return self.data_repo.get_origin_tree()

    def get_all_leaves(self, *, exclude_path: Optional[str] = None) -> List[str]:
        tree = self.get_origin_tree()
        leaves = self._list_leaves(tree)
        if exclude_path:
            leaves = [p for p in leaves if p != exclude_path]
        return sorted(leaves)

    # --- private ---

    def _list_leaves(self, node: dict, prefix: str = "") -> List[str]:
        out: List[str] = []
        for label, children in (node or {}).items():
            key = f"{prefix}/{label}" if prefix else label
            if isinstance(children, dict) and children:
                out.extend(self._list_leaves(children, key))
            else:
                out.append(key)
        return out


class IngredientsPresenter:
    """
    Liste, filtre et met en forme les ingrédients pour l'UI.
    """

    def __init__(self, ingredients_repo, data_repo, recipes_repo) -> None:
        self.ingredients_repo = ingredients_repo
        self.data_repo = data_repo
        self.recipes_repo = recipes_repo

    # ---- Listing & filtres ----

    def list_ingredients(
        self,
        *,
        query: str = "",
        cat: Optional[str] = None,
        book: Optional[str] = None,
        origin: Optional[str] = None,
    ) -> List[IngredientCardVM]:
        query = (query or "").strip().lower()
        cat = None if (cat in (None, "", "(Toutes)")) else cat
        book = None if (book in (None, "", "(Tous)")) else book
        origin = None if (origin in (None, "", "(Toutes)")) else origin

        out: List[IngredientCardVM] = []
        for ing in self.ingredients_repo.list_all():
            name = _get(ing, "name", "")
            category = _get(ing, "cat", "")
            difficulty = int(_get(ing, "difficulty", 0) or 0)
            short_effect = _get(ing, "shortEffect", None)
            effect = _get(ing, "effect", None)
            books = list(_get(ing, "books", []) or [])
            origins = list(_get(ing, "origins", []) or [])  # devrait être des libellés simples

            if cat and category != cat:
                continue
            if book and book not in books:
                continue

            if origin:
                # On accepte soit le chemin complet (au cas où), soit le dernier segment (libellé simple).
                last = origin.split("/")[-1]
                if (origin not in origins) and (last not in origins):
                    continue

            if query:
                hay = " ".join([
                    name or "",
                    category or "",
                    short_effect or "",
                    effect or "",
                    " ".join(books),
                    " ".join(origins),
                ]).lower()
                if query not in hay:
                    continue

            title = f"{name} — {category} • Diff {difficulty}"
            out.append(IngredientCardVM(
                name=name,
                title=title,
                category=category,
                difficulty=difficulty,
                short_effect=short_effect,
                effect=effect,
                books=books,
                origins=origins,
            ))
        # tri par nom
        out.sort(key=lambda vm: vm.name.lower())
        return out

    def get_filter_sources(self) -> FilterSourcesVM:
        ings = list(self.ingredients_repo.list_all())
        cats = sorted({str(_get(i, "cat", "") or "") for i in ings if _get(i, "cat", "")})
        books = list(self.data_repo.get_books())
        # Tous les libellés présents dans l'arbre (parents + feuilles)
        origins = self._list_labels(self.data_repo.get_origin_tree())
        return FilterSourcesVM(categories=cats, books=sorted(books), origins=sorted(origins))

    # ---- Utilitaires ----

    def get_ingredients_by_category(self, category: str) -> List[str]:
        names = [
            str(_get(i, "name", ""))
            for i in self.ingredients_repo.list_all()
            if str(_get(i, "cat", "")) == category
        ]
        return sorted([n for n in names if n])

    def _list_leaves(self, node: dict, prefix: str = "") -> List[str]:
        out: List[str] = []
        for label, children in (node or {}).items():
            key = f"{prefix}/{label}" if prefix else label
            if isinstance(children, dict) and children:
                out.extend(self._list_leaves(children, key))
            else:
                out.append(key)
        return out

    def _list_labels(self, node: dict) -> List[str]:
        """Retourne l'ensemble des libellés (tous les nœuds, parents + feuilles)."""
        out: List[str] = []
        def walk(n: dict):
            for k, v in (n or {}).items():
                out.append(str(k))
                if isinstance(v, dict) and v:
                    walk(v)
        walk(node or {})
        return sorted(set(out))


class RecipesPresenter:
    """
    Liste et met en forme les recettes pour l'UI.
    """

    def __init__(self, recipes_repo, ingredients_repo) -> None:
        self.recipes_repo = recipes_repo
        self.ingredients_repo = ingredients_repo

    def list_recipes(self, *, query: str = "") -> List[RecipeRowVM]:
        q = (query or "").strip().lower()
        out: List[RecipeRowVM] = []
        for r in self.recipes_repo.list_all():
            name = _get(r, "name", "")
            emoji = _get(r, "emoji", None)
            bonus = _coerce_number(_get(r, "bonus", None))
            combos = self._read_combos(r)  # alternatives de taille variable
            books = list(_get(r, "books", []) or [])

            if q:
                hay_parts = [name or "", emoji or ""]
                for c in combos:
                    hay_parts.extend(c)
                if q not in " ".join(hay_parts).lower():
                    continue

            title = f"{(emoji or '')} {name}".strip()
            out.append(RecipeRowVM(
                name=name,
                title=title,
                emoji=emoji,
                bonus=bonus,
                combos=combos,
                books=books,
            ))
        # tri alpha par nom
        out.sort(key=lambda vm: vm.name.lower())
        return out


    def get_ingredients_by_category(self, category: str) -> List[str]:
        names = [
            str(_get(i, "name", ""))
            for i in self.ingredients_repo.list_all()
            if str(_get(i, "cat", "")) == category
        ]
        return sorted([n for n in names if n])

    # --- private ---

    def _read_combos(self, recipe_obj: Any) -> List[List[str]]:
        """
        Lit recipe.combos (domain) ou recipe['ingredients'] (DTO) et
        retourne une liste d'alternatives de taille variable (>=1), sans chaînes vides.
        """
        combos = _get(recipe_obj, "combos", None)
        if combos is None:
            combos = _get(recipe_obj, "ingredients", [])
        norm: List[List[str]] = []
        for c in combos or []:
            row = [str(x or "").strip() for x in (c if isinstance(c, (list, tuple)) else [])]
            row = [x for x in row if x]
            if row:
                norm.append(row)
        return norm


class InspectionPresenter:
    """
    Fournit des sources annexes utiles pour les corrections (liste des livres, feuilles d'origines).
    Construit à partir du service d'intégrité (qui a accès aux repos).
    """

    def __init__(self, integrity_service) -> None:
        self.integrity = integrity_service

    def get_all_books(self) -> List[str]:
        books = list(self.integrity.data_repo.get_books())
        return sorted(books)

    def get_all_leaves(self) -> List[str]:
        tree = self.integrity.data_repo.get_origin_tree()
        return sorted(_list_leaves(tree))


# ---------------------------
# Internals
# ---------------------------

def _list_leaves(node: dict, prefix: str = "") -> List[str]:
    out: List[str] = []
    for label, children in (node or {}).items():
        key = f"{prefix}/{label}" if prefix else label
        if isinstance(children, dict) and children:
            out.extend(_list_leaves(children, key))
        else:
            out.append(key)
    return out


def _coerce_number(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except Exception:
        return None
