# -*- coding: utf-8 -*-
"""Families view tab for the Qt interface."""
from __future__ import annotations

from typing import Dict, List

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QHBoxLayout,
)

from .datastore import DataStore

PAD = 8
VS16 = "\ufe0f"


class ViewFamiliesTab(QWidget):
    """Display families grouped by their root emoji."""

    def __init__(self, store: DataStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.store = store

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Familles")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        layout.addWidget(self.text, 1)

        actions = QHBoxLayout()
        refresh_btn = QPushButton("Actualiser")
        refresh_btn.clicked.connect(self.refresh)
        actions.addWidget(refresh_btn)

        copy_btn = QPushButton("Copier")
        copy_btn.clicked.connect(self.copy_to_clipboard)
        actions.addWidget(copy_btn)
        actions.addStretch(1)
        layout.addLayout(actions)

        self.refresh()

    def set_store(self, store: DataStore) -> None:
        self.store = store
        self.refresh()

    def refresh(self) -> None:
        lines = self._build_grouped_lines()
        self.text.setPlainText("\n".join(lines))

    def copy_to_clipboard(self) -> None:
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.text.toPlainText())

    # --- Helpers for grouping --------------------------------------------
    def _first_grapheme(self, s: str) -> str:
        if not s:
            return ""
        if len(s) >= 2 and s[1] == VS16:
            return s[:2]
        return s[0]

    def _emoji_count_simple(self, s: str) -> int:
        return sum(1 for ch in s if ch != VS16)

    def _build_grouped_lines(self) -> List[str]:
        groups: Dict[str, List[tuple]] = {}
        for fam in self.store.families:
            root = self._first_grapheme(fam.emojis)
            indent = max(self._emoji_count_simple(fam.emojis) - 1, 0)
            label = f"{fam.emojis} : {fam.name}" if fam.name.strip() else fam.emojis
            groups.setdefault(root, []).append((indent, fam.emojis, label))

        if not groups:
            return ["(aucune famille)"]

        ordered_roots = sorted(groups.keys())
        lines: List[str] = []
        for gi, root in enumerate(ordered_roots):
            items = groups[root]
            items.sort(key=lambda item: (item[0], item[2]))
            for indent, _emojis, label in items:
                lines.append("\t" * indent + label)
            if gi < len(ordered_roots) - 1:
                lines.append("")
        return lines
