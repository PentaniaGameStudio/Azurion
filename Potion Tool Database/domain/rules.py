"""
Règles métier pures (pas d'I/O) :
- validation des catégories & combos
- calcul de difficulté totale
- détection de doublons
"""

from __future__ import annotations

from typing import Iterable, List, Protocol, Sequence, Tuple

from domain.errors import (
    ValidationError,
    CategoryError,
    NotFoundError,
    RecipeError,
)
from domain.models import Ingredient
from domain.value_objects import Category


# --------- Protocols pour découpler des repos concrets ---------

class IngredientLookup(Protocol):
    """
    Contrat minimal pour obtenir un Ingredient par son nom.
    Implémenté par les repositories d'ingrédients.
    """
    def get_by_name(self, name: str) -> Ingredient: ...
    # tolérance : certains repos ne fournissent pas get_by_name -> on peut exposer list_all
    def list_all(self) -> Iterable[Ingredient]: ...


# --------- Outils internes ---------

def _resolve_ingredient(lookup: IngredientLookup, name: str) -> Ingredient:
    """
    Résout un ingrédient par son nom via le protocole le plus simple possible.
    """
    if not name:
        raise NotFoundError("Nom d'ingrédient vide.")
    # chemin rapide si implémenté
    try:
        ing = lookup.get_by_name(name)  # type: ignore[attr-defined]
        if ing:
            return ing
    except AttributeError:
        pass
    # fallback par itération
    for i in lookup.list_all():
        if i.name == name:
            return i
    raise NotFoundError(f"Ingrédient introuvable: {name!r}")


def _norm_category(cat: str) -> str:
    try:
        return Category.normalize(cat)
    except Exception as e:
        raise CategoryError(str(e))


# --------- Règles publiques ---------

def validate_category(cat: str) -> None:
    """
    Vérifie qu'une catégorie est valide.
    """
    _ = _norm_category(cat)  # lève si invalide


# --- remplace validate_combo par cette version ---

def validate_combo(ingredient_names: Sequence[str], lookup: IngredientLookup) -> Tuple[int, int, int]:
    """
    Valide une alternative d'ingrédients de longueur libre.
    Règles:
      - Réactif: >= 1
      - Liant:   0..1
      - Cata:    0..1
      - Ingrédients doivent exister et avoir une catégorie valide.
    Retourne les compteurs (nb_liants, nb_catas, nb_reactifs).
    """
    if not isinstance(ingredient_names, (list, tuple)):
        raise RecipeError("Une alternative doit être une liste d'ingrédients.")
    if len(ingredient_names) < 1:
        raise RecipeError("Une alternative doit contenir au moins 1 ingrédient.")

    cats = []
    for n in ingredient_names:
        ing = _resolve_ingredient(lookup, n)
        cats.append(_norm_category(ing.cat))

    nb_liant = cats.count(Category.LIANT.value)
    nb_cata  = cats.count(Category.CATALYSEUR.value)
    nb_reac  = cats.count(Category.REACTIF.value)

    if nb_reac < 1:
        raise RecipeError("Chaque alternative doit contenir au moins 1 Réactif.")
    if nb_liant > 1 or nb_cata > 1:
        raise RecipeError("Au plus 1 Liant et au plus 1 Catalyseur par alternative.")

    return (nb_liant, nb_cata, nb_reac)


def total_difficulty(ingredient_names: Sequence[str], lookup: IngredientLookup) -> int:
    """
    Calcule la somme des difficultés pour une alternative donnée.
    Lève NotFoundError si un ingrédient n'existe pas.
    """
    total = 0
    for n in ingredient_names:
        ing = _resolve_ingredient(lookup, n)
        try:
            total += int(ing.difficulty)
        except Exception as _:
            # Si la donnée est corrompue, on lève une validation
            raise ValidationError(f"Difficulté invalide pour l'ingrédient {ing.name!r}.")
    return total


def find_duplicates(names: Iterable[str]) -> List[str]:
    """
    Retourne la liste des noms apparaissant au moins deux fois (ordre alpha).
    """
    seen = set()
    dups = set()
    for n in names:
        if n in seen:
            dups.add(n)
        else:
            seen.add(n)
    return sorted(dups)
