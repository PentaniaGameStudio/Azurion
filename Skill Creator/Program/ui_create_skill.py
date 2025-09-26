# -*- coding: utf-8 -*-
"""Skill creation tab using PySide6 widgets."""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QHBoxLayout,
    QRadioButton,
    QButtonGroup,
    QComboBox,
    QMessageBox,
    QPushButton,
    QCheckBox,
    QScrollArea,
)

from .datastore import DataStore
from .models import Skill
from .widgets import LabeledLineEdit, LabeledTextEdit


class CreateSkillTab(QWidget):
    """Form allowing the user to create a new skill."""

    skill_created = Signal()

    def __init__(self, store: DataStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.store = store
        self._display_to_emojis: dict[str, str] = {}

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        title = QLabel("Créer une Compétence")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        main_layout.addWidget(title)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area, 1)

        form_container = QWidget()
        scroll_area.setWidget(form_container)

        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(12)

        level_row = QHBoxLayout()
        level_label = QLabel("Niveau :")
        level_label.setStyleSheet("font-weight: bold;")
        level_row.addWidget(level_label)
        self.level_group = QButtonGroup(self)
        for label in ("Niv1", "Niv2", "Niv3"):
            btn = QRadioButton(label)
            if label == "Niv1":
                btn.setChecked(True)
            self.level_group.addButton(btn)
            level_row.addWidget(btn)
        level_row.addStretch(1)
        form_layout.addLayout(level_row)

        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        family_column = QVBoxLayout()
        family_label = QLabel("Famille *")
        family_label.setStyleSheet("font-weight: bold;")
        family_column.addWidget(family_label)
        self.family_combo = QComboBox()
        self.family_combo.setEditable(False)
        family_column.addWidget(self.family_combo)
        header_row.addLayout(family_column, 2)

        name_column = QVBoxLayout()
        name_label = QLabel("Nom *")
        name_label.setStyleSheet("font-weight: bold;")
        name_column.addWidget(name_label)
        self.name = LabeledLineEdit("", width=40)
        # remove placeholder label created by LabeledLineEdit when reused
        self.name.set_label_visible(False)
        self.name.setPlaceholderText("Nom de la compétence")
        name_column.addWidget(self.name)
        header_row.addLayout(name_column, 5)

        form_layout.addLayout(header_row)

        self._hint_label = QLabel(
            "Astuce: vous n'avez pas encore de famille. Créez-en une via le bouton 'Créer Famille'."
        )
        self._hint_label.setWordWrap(True)
        self._hint_label.setStyleSheet("color: #a33;")
        form_layout.addWidget(self._hint_label)

        diff_row = QHBoxLayout()
        diff_label = QLabel("Type :")
        diff_label.setStyleSheet("font-weight: bold;")
        diff_row.addWidget(diff_label)
        self.diff_radio_diff = QRadioButton("Difficulté")
        self.diff_radio_diff.setChecked(True)
        self.diff_radio_fac = QRadioButton("Facilité")
        self.diff_radio_passif = QRadioButton("Passif")
        diff_row.addWidget(self.diff_radio_diff)
        diff_row.addWidget(self.diff_radio_fac)
        diff_row.addWidget(self.diff_radio_passif)
        diff_row.addStretch(1)
        form_layout.addLayout(diff_row)

        self.diff_value = LabeledLineEdit("Valeur (ex: -2 aux jets d'attaque)")
        form_layout.addWidget(self.diff_value)

        self.cost = LabeledLineEdit("Coût")
        self.target = LabeledLineEdit("Cible")
        self.range_ = LabeledLineEdit("Portée")
        self.duration = LabeledLineEdit("Durée")
        self.damage = LabeledLineEdit("Dégâts")

        for widget in (self.cost, self.target, self.range_, self.duration, self.damage):
            form_layout.addWidget(widget)

        self.effects = LabeledTextEdit("Effet(s)")
        self.conditions = LabeledTextEdit("Condition(s)")
        self.limits = LabeledTextEdit("Limite(s)")

        form_layout.addWidget(self.effects)
        form_layout.addWidget(self.conditions)
        form_layout.addWidget(self.limits)

        self.hidden_checkbox = QCheckBox("Masquer dans les index (hided)")
        form_layout.addWidget(self.hidden_checkbox)

        button_row = QHBoxLayout()
        save_btn = QPushButton("Enregistrer")
        save_btn.clicked.connect(self._save)
        button_row.addWidget(save_btn)

        clear_btn = QPushButton("Vider le formulaire")
        clear_btn.clicked.connect(self._clear)
        button_row.addWidget(clear_btn)

        refresh_btn = QPushButton("Rafraîchir familles")
        refresh_btn.clicked.connect(self.refresh_families)
        button_row.addWidget(refresh_btn)

        button_row.addStretch(1)
        main_layout.addLayout(button_row)

        self.refresh_families()

    def set_store(self, store: DataStore) -> None:
        self.store = store
        self.refresh_families()

    def refresh_families(self) -> None:
        current_display = self.family_combo.currentText()
        pairs = self._build_family_choices()
        values = [display for display, _ in pairs]
        self._display_to_emojis = {display: emojis for display, emojis in pairs}

        self.family_combo.blockSignals(True)
        self.family_combo.clear()
        self.family_combo.addItems(values)
        self.family_combo.blockSignals(False)

        if values:
            if current_display in values:
                self.family_combo.setCurrentIndex(values.index(current_display))
            elif self.family_combo.currentIndex() < 0:
                self.family_combo.setCurrentIndex(0)
        self._hint_label.setVisible(not bool(values))

    def _build_family_choices(self) -> list[tuple[str, str]]:
        pairs: list[tuple[str, str]] = []
        for fam in self.store.families:
            display = f"{fam.emojis} — {fam.name}" if fam.name.strip() else fam.emojis
            pairs.append((display, fam.emojis))
        pairs.sort(key=lambda item: item[0])
        return pairs

    def _clear(self) -> None:
        self.name.setText("")
        self.diff_radio_diff.setChecked(True)
        self.diff_value.setText("")
        for widget in (self.cost, self.target, self.range_, self.duration, self.damage):
            widget.setText("")
        self.effects.clear()
        self.conditions.clear()
        self.limits.clear()
        self.hidden_checkbox.setChecked(False)
        if self.family_combo.count() > 0:
            self.family_combo.setCurrentIndex(0)
        for btn in self.level_group.buttons():
            if btn.text() == "Niv1":
                btn.setChecked(True)
                break

    def _save(self) -> None:
        display = self.family_combo.currentText().strip()
        family_emojis = self._display_to_emojis.get(display, "").strip()
        if not family_emojis:
            QMessageBox.warning(self, "Famille requise", "Merci de choisir une famille.")
            return

        name = self.name.text().strip()
        if not name:
            QMessageBox.warning(self, "Nom requis", "La compétence doit avoir un nom.")
            return

        if self.diff_radio_fac.isChecked():
            diff_label = "Facilité"
        elif self.diff_radio_passif.isChecked():
            diff_label = "Passif"
        else:
            diff_label = "Difficulté"
        diff_text = self.diff_value.text().strip()
        difficulty_field = f"{diff_label} : {diff_text}" if diff_text else diff_label

        level_button = self.level_group.checkedButton()
        level = level_button.text() if level_button else "Niv1"

        skill = Skill(
            family=family_emojis,
            name=name,
            cost=self.cost.text().strip(),
            difficulty=difficulty_field,
            target=self.target.text().strip(),
            range_=self.range_.text().strip(),
            damage=self.damage.text().strip(),
            effects=self.effects.get_lines(),
            conditions=self.conditions.get_lines(),
            limits=self.limits.get_lines(),
            duration=self.duration.text().strip(),
            level=level,
            hided=self.hidden_checkbox.isChecked(),
        )

        try:
            self.store.add_skill(skill)
            QMessageBox.information(self, "OK", f"Compétence '{name}' ajoutée.")
            self._clear()
            self.skill_created.emit()
        except Exception as exc:
            QMessageBox.critical(self, "Erreur", str(exc))
