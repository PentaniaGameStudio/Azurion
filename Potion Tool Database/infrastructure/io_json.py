"""
Lecture/écriture JSON avec sauvegarde .bak et écriture atomique.
"""

from __future__ import annotations

import json
from typing import Any, List

from domain.errors import RepositoryError
from .paths import ensure_parent_dir, atomic_write_text, make_backup


def read_json_file(path: str, *, expect_list: bool = False) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if expect_list and not isinstance(data, list):
            raise RepositoryError(f"Fichier JSON '{path}' invalide: liste attendue.")
        return data
    except FileNotFoundError:
        if expect_list:
            return []
        raise
    except Exception as e:
        raise RepositoryError(f"Lecture JSON échouée pour '{path}': {e}") from e


def write_json_file(path: str, data: Any) -> None:
    """
    Ecrit joliment formatté, non-ASCII préservé, avec .bak et écriture atomique.
    """
    try:
        ensure_parent_dir(path)
        # Sauvegarde
        make_backup(path)
        # Dump beau
        text = json.dumps(data, ensure_ascii=False, indent=2)
        atomic_write_text(path, text)
    except Exception as e:
        raise RepositoryError(f"Écriture JSON échouée pour '{path}': {e}") from e
