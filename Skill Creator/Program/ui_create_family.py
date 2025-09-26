# -*- coding: utf-8 -*-
"""Family creation tab implemented with Qt widgets."""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
)

from .datastore import DataStore
from .models import Family
from .widgets import LabeledLineEdit


class CreateFamilyTab(QWidget):
    """Form that lets the user create a new family."""

    family_created = Signal()

    def __init__(self, store: DataStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.store = store

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Créer une Famille")
        title.setObjectName("titleLabel")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        self.emojis = LabeledLineEdit("Emojis (clé) — ex: 🌊🔊", width=30)
        self.name = LabeledLineEdit("Nom de la famille", width=40)

        layout.addWidget(self.emojis)
        layout.addWidget(self.name)

        buttons = QHBoxLayout()
        save_btn = QPushButton("Enregistrer")
        save_btn.clicked.connect(self._save)
        buttons.addWidget(save_btn)

        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(self._clear_all)
        buttons.addWidget(cancel_btn)

        buttons.addStretch(1)
        layout.addLayout(buttons)

    def set_store(self, store: DataStore) -> None:
        self.store = store

    def _clear_keep_emojis(self) -> None:
        self.name.setText("")

    def _clear_all(self) -> None:
        self.emojis.setText("")
        self.name.setText("")

    def _save(self) -> None:
        emojis = self.emojis.text().strip()
        name = self.name.text().strip()

        if not emojis:
            QMessageBox.warning(self, "Champ requis", "Les emojis (clé) sont obligatoires.")
            return
        try:
            self.store.add_family(Family(emojis=emojis, name=name, description=""))
            QMessageBox.information(self, "OK", f"Famille '{emojis}' ajoutée.")
            self._clear_keep_emojis()
            self.family_created.emit()
        except Exception as exc:
            QMessageBox.critical(self, "Erreur", str(exc))
