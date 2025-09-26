"""
Utilitaires de chemins et d'écriture atomique avec sauvegarde .bak.
"""

from __future__ import annotations

import os
import tempfile
import time
from typing import Optional


def ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)


def atomic_write_text(path: str, text: str, *, encoding: str = "utf-8") -> None:
    """
    Écrit *atomiquement* : dans un fichier temporaire puis remplace le fichier cible.
    """
    dirpath = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp_path = tempfile.mkstemp(prefix=".tmp_", dir=dirpath, text=True)
    try:
        with os.fdopen(fd, "w", encoding=encoding, newline="") as f:
            f.write(text)
        os.replace(tmp_path, path)  # atomic move
    except Exception:
        # nettoyer si erreur
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
        raise


def make_backup(path: str, *, suffix: Optional[str] = None, overwrite_single: bool = True) -> Optional[str]:
    """
    Crée une sauvegarde .bak avant écriture.
    - overwrite_single=True : utilise 'file.bak' (remplacé à chaque fois)
    - sinon : timestamp suffixé 'file.20250101-120102.bak'
    Retourne le chemin du .bak créé ou None si pas de fichier original.
    """
    if not os.path.exists(path):
        return None
    base = os.path.abspath(path)
    if suffix:
        bak = f"{base}.{suffix}.bak"
    elif overwrite_single:
        bak = f"{base}.bak"
    else:
        ts = time.strftime("%Y%m%d-%H%M%S")
        bak = f"{base}.{ts}.bak"
    try:
        # copy fichier binaire (mais on l'utilise pour texte)
        with open(base, "rb") as src, open(bak, "wb") as dst:
            dst.write(src.read())
        return bak
    except Exception:
        # si la sauvegarde échoue, on n'empêche pas l'écriture (mais c'est loggable côté appelant)
        return None
