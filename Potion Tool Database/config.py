"""
Configuration simple pour Potion DB Tool.

- Recherche optionnelle d'un fichier 'potion_db_tool.config.json' dans le cwd.
- Valeurs par défaut : ingredients.json, recipes.json, data.js dans le cwd.
- Thème PySimpleGUI configurable (par défaut: 'DarkBlue14').
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class Config:
    ingredients_path: str
    recipes_path: str
    data_js_path: str
    sg_theme: str = "DarkBlue14"

    @staticmethod
    def load() -> "Config":
        """
        Charge la config depuis 'potion_db_tool.config.json' si présent,
        sinon utilise les chemins par défaut relatifs au cwd.
        """
        cfg_path = os.path.join(os.getcwd(), "potion_db_tool.config.json")
        data: Dict[str, Any] = {}
        if os.path.isfile(cfg_path):
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                # silencieux : si corrompu, on retombe sur défauts
                data = {}

        ingredients_path = os.path.abspath(str(data.get("ingredients_path", "ingredients.json")))
        recipes_path = os.path.abspath(str(data.get("recipes_path", "recipes.json")))
        data_js_path = os.path.abspath(str(data.get("data_js_path", "data.js")))
        sg_theme = str(data.get("sg_theme", "DarkBlue14"))

        return Config(
            ingredients_path=ingredients_path,
            recipes_path=recipes_path,
            data_js_path=data_js_path,
            sg_theme=sg_theme,
        )
