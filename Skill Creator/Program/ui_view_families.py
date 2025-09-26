# -*- coding: utf-8 -*-
"""
///summary
Vue texte des familles : groupées par 1er emoji, indentation = nb d’emojis - 1,
1 famille par ligne, ligne vide entre groupes.
"""
import tkinter as tk
from tkinter import ttk
from typing import List, Dict
from .datastore import DataStore

PAD = 8
VS16 = "\ufe0f"  # variation selector-16, présent dans beaucoup d’émojis (⚔️, ⚒️, etc.)

class ViewFamiliesFrame(ttk.Frame):
    def __init__(self, master, store: DataStore):
        super().__init__(master, padding=PAD)
        self.store = store

        ttk.Label(self, text="Familles", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, PAD))

        # Zone texte read-only
        self.text = tk.Text(self, height=18, wrap="word")
        self.text.configure(state="disabled")
        self.text.pack(fill="both", expand=True)

        # Barre d’actions (Actualiser + Copier)
        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=(PAD, 0))
        ttk.Button(actions, text="Actualiser", command=self.refresh).pack(side="left")
        ttk.Button(actions, text="Copier", command=self.copy_to_clipboard).pack(side="left", padx=(PAD, 0))

        self.refresh()

    # --- Helpers unicode / emojis -------------------------------------------

    def _first_grapheme(self, s: str) -> str:
        """Retourne le 1er emoji (grapheme approx.) = 1er codepoint + VS16 éventuel."""
        if not s:
            return ""
        if len(s) >= 2 and s[1] == VS16:
            return s[:2]
        return s[0]

    def _emoji_count_simple(self, s: str) -> int:
        """
        Compte grossièrement les emojis comme 'nb de codepoints != VS16'.
        Suffisant pour des emojis simples (⚔️, ⚒️, ✨, 🐉, etc.).
        """
        return sum(1 for ch in s if ch != VS16)

    # --- Construction des lignes --------------------------------------------

    def _build_grouped_lines(self) -> List[str]:
        """
        Construit les lignes formatées :
        - Groupées par 1er emoji (root)
        - Indentation = nb_emojis(s) - 1 (tabulation par niveau)
        - Ligne vide entre groupes, pas entre items du même groupe
        - Format d’une ligne : "<emojis> : <nom>" (si nom vide => juste <emojis>)
        """
        # Regrouper par racine (1er emoji)
        groups: Dict[str, List[tuple]] = {}
        for fam in self.store.families:
            root = self._first_grapheme(fam.emojis)
            indent = max(self._emoji_count_simple(fam.emojis) - 1, 0)
            label = f"{fam.emojis} : {fam.name}" if fam.name.strip() else fam.emojis
            groups.setdefault(root, []).append((indent, fam.emojis, label))

        if not groups:
            return ["(aucune famille)"]

        # Ordonner les groupes par racine (clé) et trier les items du groupe :
        #   1) indent asc (la base d’abord), 2) label alpha pour stabilité
        ordered_roots = sorted(groups.keys())
        lines: List[str] = []
        for gi, root in enumerate(ordered_roots):
            items = groups[root]
            items.sort(key=lambda t: (t[0], t[2]))
            for indent, _emojis, label in items:
                lines.append("\t" * indent + label)
            if gi < len(ordered_roots) - 1:
                lines.append("")  # ligne vide entre groupes
        return lines

    # --- Actions UI ----------------------------------------------------------

    def refresh(self):
        lines = self._build_grouped_lines()
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", "\n".join(lines))
        self.text.configure(state="disabled")

    def copy_to_clipboard(self):
        self.clipboard_clear()
        self.clipboard_append(self.text.get("1.0", "end").rstrip("\n"))
