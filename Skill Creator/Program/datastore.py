# -*- coding: utf-8 -*-
"""
///summary
Couche de persistance JSON pour familles et compétences.
"""
import json, os, sys
from typing import List, Dict, Any, Optional
from .models import Family, Skill

DATA_FILENAME = "skills_data.json"

def resource_path(relative: str) -> str:
    try:
        base_path = sys._MEIPASS  # type: ignore
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative)

class DataStore:
    """
    ///summary
    Gère le chargement/enregistrement dans un JSON.
    Schema:
    {
        "families":[{emojis,name,description}], 
        "skills":[{family,name,cost,difficulty,target,range_,damage,effects,conditions,limits}]
    }
    """
    def __init__(self, path: Optional[str] = None):
        self.path = path or resource_path(DATA_FILENAME)
        self.families: List[Family] = []
        self.skills: List[Skill] = []
        self._ensure_file()

    def _ensure_file(self) -> None:
        if not os.path.exists(self.path):
            self._write({"families": [], "skills": []})
        self._read_into_memory()

    def _write(self, payload: Dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def _read_into_memory(self) -> None:
        with open(self.path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        self.families = [Family(**fam) for fam in raw.get("families", [])]
        converted = []
        for s in raw.get("skills", []):
            if "range" in s and "range_" not in s:
                s["range_"] = s.pop("range")
            converted.append(Skill(**s))
        self.skills = converted

    def save(self) -> None:
        payload = {
            "families": [Family(**f.__dict__).__dict__ for f in self.families],
            "skills": [Skill(**s.__dict__).__dict__ for s in self.skills],
        }
        self._write(payload)

    # Ops
    def add_family(self, fam: Family) -> None:
        if any(f.emojis == fam.emojis for f in self.families):
            raise ValueError(f"La famille '{fam.emojis}' existe déjà.")
        self.families.append(fam)
        self.save()

    def add_skill(self, skill: Skill) -> None:
        self.skills.append(skill)
        self.save()

    def get_family_emojis(self):
        return [f.emojis for f in self.families]
