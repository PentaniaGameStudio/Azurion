"""
Mapping Domain <-> DTO (JSON/JS) pour les repositories.
Respecte la structure actuelle des fichiers:
- ingredients.json : [{ name, cat, difficulty, shortEffect, effect, origins[], books[] }]
- recipes.json     : [{ emoji, name, ingredients:[[liant, cata, react], ...], bonus }]
- data.js          : exports ORIGIN_TREE (dict imbriqué) et BOOKS (array de titres)
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Any, Dict, List, Mapping, Sequence

# Domain models (snakes case)
from domain.models import Ingredient, Recipe


# ---------------
# INGREDIENTS
# ---------------

def ingredient_to_dto(ing: Ingredient) -> Dict[str, Any]:
    """
    Domain Ingredient -> DTO conforme à ingredients.json
    """
    # On force l'ordre des clés (Python >=3.7 respecte l'ordre d'insertion)
    dto = OrderedDict()
    dto["name"] = ing.name
    dto["cat"] = ing.cat
    dto["difficulty"] = int(ing.difficulty)
    dto["shortEffect"] = ing.short_effect or ""
    dto["effect"] = ing.effect or ""
    dto["origins"] = list(ing.origins or [])
    dto["books"] = list(ing.books or [])
    return dict(dto)


def ingredient_from_dto(d: Mapping[str, Any]) -> Ingredient:
    """
    DTO -> Domain Ingredient (normalisation minimale).
    """
    return Ingredient(
        name=str(d.get("name", "")).strip(),
        cat=str(d.get("cat", "")).strip(),
        difficulty=int(d.get("difficulty", 0) or 0),
        short_effect=_norm_empty(d.get("shortEffect")),
        effect=_norm_empty(d.get("effect")),
        origins=list(d.get("origins", []) or []),
        books=list(d.get("books", []) or []),
    )


# ---------------
# RECIPES
# ---------------

def recipe_to_dto(rec: Recipe) -> Dict[str, Any]:
    """
    Domain Recipe -> DTO conforme à recipes.json
    (le champ Domain .combos devient DTO .ingredients)
    """
    dto = OrderedDict()
    dto["emoji"] = rec.emoji or ""
    dto["name"] = rec.name
    dto["desc"] = rec.desc
    dto["ingredients"] = [list(combo) for combo in (rec.combos or [])]
    dto["books"] = list(rec.books) if getattr(rec, "books", None) else []
    dto["bonus"] = rec.bonus if rec.bonus is not None else ""
    return dict(dto)


def recipe_from_dto(d: Mapping[str, Any]) -> Recipe:
    combos_raw = list(d.get("ingredients", []) or [])
    norm: List[List[str]] = []
    for c in combos_raw:
        row = [str(x or "").strip() for x in (c if isinstance(c, (list, tuple)) else [])]
        row = [x for x in row if x]  # supprime vides
        if row:
            norm.append(row)

    bonus = d.get("bonus", "")
    bonus_val = None
    try:
        if bonus not in ("", None):
            bonus_val = float(bonus)
    except Exception:
        bonus_val = None
    books = list(d.get("books") or [])

    return Recipe(
        name=str(d.get("name", "")).strip(),
        desc=str(d.get("desc", "")).strip(),
        emoji=_norm_empty(d.get("emoji")),
        bonus=bonus_val,
        combos=norm,
        books=books
    )

# ---------------
# DATA.JS (ORIGINS & BOOKS)
# ---------------
# Le parsing/écriture JS sera effectué dans infrastructure.io_jsdata
# Mapping ici se contente d'exposer les structures Python (dict/list).

def ensure_origin_tree(tree: Any) -> Dict[str, Any]:
    """
    Défense simple : garantir un dict imbriqué (valeurs non-dict -> feuilles vides).
    """
    if not isinstance(tree, dict):
        return {}
    out: Dict[str, Any] = {}
    for k, v in tree.items():
        if isinstance(v, dict):
            out[str(k)] = ensure_origin_tree(v)
        else:
            out[str(k)] = {}
    return out


def ensure_books_list(books: Sequence[Any]) -> List[str]:
    return [str(x) for x in (books or [])]


# ---------------
# Utils
# ---------------

def _norm_empty(val: Any) -> str | None:
    if val in ("", None):
        return None
    s = str(val).strip()
    return s if s else None
