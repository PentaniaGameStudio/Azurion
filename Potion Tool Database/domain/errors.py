"""
Arbre d'exceptions métier pour Potion DB Tool.
Aucune dépendance UI ; ces erreurs sont interceptées par l'application.
"""

from __future__ import annotations


# Base
class PotionDBError(Exception):
    """Erreur générique de domaine."""


# Validation / intégrité
class ValidationError(PotionDBError):
    """Données invalides (contrainte métier)."""


class IntegrityError(PotionDBError):
    """Incohérence de dataset (références cassées, etc.)."""


# Spécifiques
class NotFoundError(PotionDBError):
    """Ressource introuvable."""


class DuplicateNameError(ValidationError):
    """Nom déjà utilisé (ingrédient/recette/livre)."""


class CategoryError(ValidationError):
    """Catégorie invalide."""


class OriginError(ValidationError):
    """Origine invalide (non-feuille ou absente)."""


class BookError(ValidationError):
    """Livre invalide (référence manquante)."""


class RecipeError(ValidationError):
    """Recette invalide (combos, ingrédients manquants…)."""


# Infrastructure
class RepositoryError(PotionDBError):
    """Erreur d'accès dépôt (I/O, parsing…)."""
