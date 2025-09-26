# -*- coding: utf-8 -*-
"""Main window for the Skill Creator Qt application."""
from __future__ import annotations

import json
import os
from typing import Optional

from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QToolButton,
    QFileDialog,
)
from qt_material import apply_stylesheet

from .datastore import DataStore
from .ui_create_family import CreateFamilyTab
from .ui_create_skill import CreateSkillTab
from .ui_view_skills import ViewSkillsTab
from .ui_view_families import ViewFamiliesTab


class MainWindow(QMainWindow):
    """Main window hosting the different application tabs."""

    THEMES = ("red", "pink", "purple", "blue", "cyan", "teal", "lightgreen", "yellow", "amber")

    def __init__(self, store: DataStore, app: QApplication, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Skill Utility")
        self.resize(1100, 720)

        self.app = app
        self.store = store

        self.settings = QSettings("UnifoxGameStudio", "SkillCreator")
        self._is_dark = self.settings.value("ui/is_dark", True, type=bool)
        self._theme_color = self.settings.value("ui/theme_color", "teal", type=str)
        self._apply_theme_values(self._is_dark, self._theme_color)

        self._tabs = QTabWidget(self)
        self._tabs.setDocumentMode(True)
        self._tabs.setStyleSheet(
            """
            QTabBar::tab {
                height: 40px;
                padding: 8px 16px;
                font-size: 12.5px;
            }
            """
        )
        self.setCentralWidget(self._tabs)

        self.tab_create_family = CreateFamilyTab(self.store)
        self.tab_create_skill = CreateSkillTab(self.store)
        self.tab_view_skills = ViewSkillsTab(self.store)
        self.tab_view_families = ViewFamiliesTab(self.store)

        self._tabs.addTab(self.tab_view_skills, "Afficher Compétences")
        self._tabs.addTab(self.tab_create_skill, "Créer Compétence")
        self._tabs.addTab(self.tab_create_family, "Créer Famille")
        self._tabs.addTab(self.tab_view_families, "Afficher Familles")

        self.tab_create_family.family_created.connect(self._on_family_created)
        self.tab_create_skill.skill_created.connect(self._on_skill_created)

        self._tabs.currentChanged.connect(self._maybe_refresh)

        corner = QWidget(self)
        hlay = QHBoxLayout(corner)
        hlay.setContentsMargins(0, 0, 8, 0)
        hlay.setSpacing(6)

        self._btn_theme = QToolButton(corner)
        self._btn_theme.setCursor(Qt.PointingHandCursor)
        self._btn_theme.setToolTip("Basculer le thème (Dark/Light)")
        self._btn_theme.clicked.connect(self._toggle_theme)
        self._btn_theme.setStyleSheet("QToolButton { padding: 6px 14px; }")
        hlay.addWidget(self._btn_theme)

        self._btn_config = QToolButton(corner)
        self._btn_config.setCursor(Qt.PointingHandCursor)
        self._btn_config.setText("⚙️ Config")
        self._btn_config.setToolTip("Ouvrir les préférences (couleur, Dark/Light, etc.)")
        self._btn_config.clicked.connect(self._open_config_dialog)
        self._btn_config.setStyleSheet("QToolButton { padding: 6px 14px; }")
        hlay.addWidget(self._btn_config)

        corner.setFixedHeight(46)
        self._tabs.setCornerWidget(corner, Qt.TopRightCorner)

        self._apply_theme()
        self._update_theme_button_caption()

        self._build_menu()

    # ----- UI helpers -----------------------------------------------------
    def _build_menu(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu("Fichier")
        file_menu.addAction(self._create_action("Ouvrir un JSON…", self._load_other_file))
        file_menu.addAction(self._create_action("Exporter JSON sous…", self._export_as))
        file_menu.addSeparator()
        file_menu.addAction(self._create_action("Quitter", self.close))

        help_menu = menubar.addMenu("Aide")
        help_menu.addAction(self._create_action("À propos", self._about))

    def _create_action(self, text: str, slot) -> QAction:
        act = QAction(text, self)
        act.triggered.connect(slot)
        return act

    def _maybe_refresh(self, idx: int) -> None:
        widget = self._tabs.widget(idx)
        if hasattr(widget, "refresh"):
            try:
                widget.refresh()
            except Exception:
                pass

    # ----- Theme handling -------------------------------------------------
    def _toggle_theme(self) -> None:
        self._is_dark = not self._is_dark
        self._apply_theme()
        self._update_theme_button_caption()
        self.settings.setValue("ui/is_dark", self._is_dark)

    def _apply_theme(self) -> None:
        self._apply_theme_values(self._is_dark, self._theme_color)

    def _apply_theme_values(self, is_dark: bool, color: str) -> None:
        chosen = (color or "blue").lower()
        if chosen not in self.THEMES:
            chosen = "blue"
        theme_name = f"{'dark' if is_dark else 'light'}_{chosen}.xml"
        try:
            apply_stylesheet(self.app, theme=theme_name, invert_secondary=(not is_dark and False))
        except Exception:
            apply_stylesheet(self.app, theme='dark_blue.xml' if is_dark else 'light_blue.xml')

    def _preview_theme(self, *, is_dark: Optional[bool] = None, color: Optional[str] = None) -> None:
        tmp_dark = self._is_dark if is_dark is None else is_dark
        tmp_color = self._theme_color if color is None else color
        self._apply_theme_values(tmp_dark, tmp_color)

    def _update_theme_button_caption(self) -> None:
        if hasattr(self, "_btn_theme") and self._btn_theme:
            self._btn_theme.setText("🌙 Dark" if self._is_dark else "☀️ Light")

    def _open_config_dialog(self) -> None:
        dlg = _ConfigDialog(self)
        if dlg.exec():
            is_dark, color = dlg.values()
            changed = (is_dark != self._is_dark) or (color != self._theme_color)
            self._is_dark = is_dark
            self._theme_color = color
            if changed:
                self._apply_theme()
                self._update_theme_button_caption()
                self.settings.setValue("ui/is_dark", self._is_dark)
                self.settings.setValue("ui/theme_color", self._theme_color)
                self._maybe_refresh(self._tabs.currentIndex())

    # ----- Data handling --------------------------------------------------
    def _on_family_created(self) -> None:
        self.tab_create_skill.refresh_families()
        self.tab_view_families.refresh()

    def _on_skill_created(self) -> None:
        self.tab_view_skills.refresh()

    def _set_store(self, store: DataStore) -> None:
        self.store = store
        for tab in (self.tab_create_family, self.tab_create_skill, self.tab_view_skills, self.tab_view_families):
            tab.set_store(store)
        self.tab_create_skill.refresh_families()
        self.tab_view_skills.refresh()
        self.tab_view_families.refresh()

    # ----- Menu actions ---------------------------------------------------
    def _load_other_file(self) -> None:
        initial_dir = os.path.dirname(self.store.path) if self.store.path else os.getcwd()
        path, _ = QFileDialog.getOpenFileName(self, "Ouvrir un JSON", initial_dir, "JSON files (*.json)")
        if not path:
            return
        try:
            new_store = DataStore(path=path)
            self._set_store(new_store)
            QMessageBox.information(self, "Ouvert", f"Fichier chargé:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger le fichier:\n{exc}")

    def _export_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter JSON",
            os.path.join(os.path.dirname(self.store.path), "skills_data_export.json"),
            "JSON files (*.json)",
        )
        if not path:
            return
        try:
            payload = {
                "families": [f.__dict__ for f in self.store.families],
                "skills": [s.__dict__ for s in self.store.skills],
            }
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "Exporté", f"Données exportées vers:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Erreur", f"Export impossible:\n{exc}")

    def _about(self) -> None:
        QMessageBox.information(
            self,
            "À propos",
            (
                "Skill Utility (édition Qt)\n\n"
                "Créer des familles, créer des compétences,\n"
                "afficher les compétences et lister les familles.\n\n"
                "Fichier: skills_data.json (dans le dossier du package)"
            ),
        )


class _ConfigDialog(QDialog):
    """Configuration dialog for theme selection."""

    def __init__(self, parent: MainWindow):
        super().__init__(parent)
        self.setWindowTitle("Préférences")
        self.setModal(True)

        lay = QVBoxLayout(self)

        self._orig_dark = parent._is_dark
        self._orig_color = parent._theme_color

        self.chk_dark = QCheckBox("Mode sombre (Dark)")
        self.chk_dark.setChecked(parent._is_dark)
        lay.addWidget(self.chk_dark)

        row = QHBoxLayout()
        row.addWidget(QLabel("Couleur d'accent :"))
        self.cmb_color = QComboBox()
        self.cmb_color.addItems(parent.THEMES)
        try:
            idx = parent.THEMES.index(parent._theme_color)
        except ValueError:
            idx = parent.THEMES.index("blue")
        self.cmb_color.setCurrentIndex(idx)
        row.addWidget(self.cmb_color, 1)
        lay.addLayout(row)

        self.chk_dark.toggled.connect(
            lambda value: parent._preview_theme(is_dark=value, color=self.cmb_color.currentText())
        )
        self.cmb_color.currentTextChanged.connect(
            lambda color: parent._preview_theme(is_dark=self.chk_dark.isChecked(), color=color)
        )

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)

        self.rejected.connect(self._restore_original_theme)

    def _restore_original_theme(self) -> None:
        parent: MainWindow = self.parent()  # type: ignore
        parent._apply_theme_values(self._orig_dark, self._orig_color)
        parent._update_theme_button_caption()

    def accept(self) -> None:
        parent: MainWindow = self.parent()  # type: ignore
        parent._is_dark, parent._theme_color = self.values()
        parent._apply_theme()
        parent._update_theme_button_caption()
        parent.settings.setValue("ui/is_dark", parent._is_dark)
        parent.settings.setValue("ui/theme_color", parent._theme_color)
        parent._maybe_refresh(parent._tabs.currentIndex())
        super().accept()

    def reject(self) -> None:
        self._restore_original_theme()
        super().reject()

    def values(self) -> tuple[bool, str]:
        return self.chk_dark.isChecked(), self.cmb_color.currentText()
