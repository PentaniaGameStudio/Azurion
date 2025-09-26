# -*- coding: utf-8 -*-
"""
///summary
Modèles de données pour Famille et Compétence.
"""
from dataclasses import dataclass, field, asdict
from typing import List

@dataclass
class Family:
    """Famille de compétences (clé émoji + nom lisible)."""
    emojis: str
    name: str
    description: str = ""

@dataclass
class Skill:
    """Compétence (tous champs en string, listes pour effet/conditions/limites)."""
    # ///summary: Ordre conforme au besoin utilisateur.
    hided: bool = False
    family: str = ""
    name: str = ""
    level: str = "Niv1"
    cost: str = ""
    difficulty: str = ""
    target: str = ""
    range_: str = ""
    duration: str = ""
    damage: str = ""
    effects: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    limits: List[str] = field(default_factory=list)

    def to_row(self) -> List[str]:
        return [self.family, self.name, self.cost, self.target, self.range_, self.damage]

def asdict_family(f: Family):
    return asdict(f)

def asdict_skill(s: Skill):
    return asdict(s)
