# UI/main_window.py
from __future__ import annotations
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QToolButton, QDialog, QVBoxLayout,
    QHBoxLayout, QLabel, QComboBox, QCheckBox, QDialogButtonBox
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QIcon
from qt_material import apply_stylesheet

from UI.tabs.inspection import InspectionTab
from UI.tabs.ingredients import IngredientsTab
from UI.tabs.recipes import RecipesTab
from UI.tabs.books import BooksTab
from UI.tabs.origins import OriginsTab

class MainWindow(QMainWindow):
    THEMES = ("red", "pink", "purple", "blue", "cyan", "teal", "lightgreen", "yellow", "amber")
    
    def __init__(self, cfg, container, app, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Potion Database Tool")
        self.resize(1200, 800)

        # --- stocker app AVANT toute utilisation ---
        self.app = app
        self.cfg = cfg
        self.container = container

        # --- charger les préférences avant d'appliquer le thème ---
        self.settings = QSettings("UnifoxGameStudio", "PotionDBTool")
        self._is_dark = self.settings.value("ui/is_dark", True, type=bool)
        self._theme_color = self.settings.value("ui/theme_color", "teal", type=str)
        # **NE PAS** appeler _update_theme_button_caption ici (le bouton n’existe pas encore)
        self._apply_theme()

        # Tabs
        self._tabs = QTabWidget(self)
        self.setCentralWidget(self._tabs)
        self._tabs.setStyleSheet("""
            QTabBar::tab {
                height: 40px;
                padding: 8px 16px;
                font-size: 12.5px;
            }
            """)

        self._tab_inspection = InspectionTab(container)
        self._tabs.addTab(self._tab_inspection, QIcon(), "Analyse")

        self._tab_ingredients = IngredientsTab(container)
        self._tabs.addTab(self._tab_ingredients, QIcon(), "Ingrédients")

        self._tab_recipes = RecipesTab(container)
        self._tabs.addTab(self._tab_recipes, QIcon(), "Recettes")

        self._tab_books = BooksTab(container)
        self._tabs.addTab(self._tab_books, QIcon(), "Livres")

        self._tab_origins = OriginsTab(container)
        self._tabs.addTab(self._tab_origins, QIcon(), "Origines")

        self._tabs.currentChanged.connect(self._maybe_refresh)

        # ----- Panneau corner: [Dark/Light] [Config] -----
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

        # maintenant que les boutons existent, on peut MAJ le libellé et appliquer thème
        self._apply_theme()
        self._update_theme_button_caption()

        # maintenant que le bouton existe, on peut MAJ le libellé
        self._update_theme_button_caption()

    def _maybe_refresh(self, idx: int):
        w: QWidget = self._tabs.widget(idx)
        if hasattr(w, "refresh"):
            try:
                w.refresh()
            except Exception:
                pass

    # ----- Thème -----
    def _toggle_theme(self):
        self._is_dark = not self._is_dark
        self._apply_theme()
        self._update_theme_button_caption()
        self.settings.setValue("ui/is_dark", self._is_dark)

    def _apply_theme(self):
        """Applique le thème courant (valeurs persistées dans self._is_dark/_theme_color)."""
        self._apply_theme_values(self._is_dark, self._theme_color)

    def _apply_theme_values(self, is_dark: bool, color: str):
        """Applique un thème donné SANS toucher aux préférences (utile pour l'aperçu live)."""
        c = (color or "blue").lower()
        if c not in self.THEMES:
            c = "blue"
        theme_name = f"{'dark' if is_dark else 'light'}_{c}.xml"
        try:
            apply_stylesheet(self.app, theme=theme_name, invert_secondary=(not is_dark and False))
        except Exception:
            # fallback sûr
            apply_stylesheet(self.app, theme='dark_blue.xml' if is_dark else 'light_blue.xml')

    def _preview_theme(self, *, is_dark: bool | None = None, color: str | None = None):
        """
        Aperçu immédiat dans la fenêtre, sans modifier self._is_dark/_theme_color ni QSettings.
        Appelé par la boîte Config à chaque changement.
        """
        tmp_dark = self._is_dark if is_dark is None else is_dark
        tmp_color = self._theme_color if color is None else color
        self._apply_theme_values(tmp_dark, tmp_color)



    def _update_theme_button_caption(self):
        if hasattr(self, "_btn_theme") and self._btn_theme:
            self._btn_theme.setText("🌙 Dark" if self._is_dark else "☀️ Light")

    def _open_config_dialog(self):
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
                    # rafraîchir l’onglet courant pour refléter styles éventuels
                    self._maybe_refresh(self._tabs.currentIndex())


class _ConfigDialog(QDialog):
    def __init__(self, parent: MainWindow):
        super().__init__(parent)
        self.setWindowTitle("Préférences")
        self.setModal(True)
        lay = QVBoxLayout(self)

        # --- mémoriser l'état initial pour pouvoir restaurer si 'Annuler' ---
        self._orig_dark = parent._is_dark
        self._orig_color = parent._theme_color

        # Dark/Light
        self.chk_dark = QCheckBox("Mode sombre (Dark)")
        self.chk_dark.setChecked(parent._is_dark)
        lay.addWidget(self.chk_dark)

        # Couleur
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

        # --- aperçu live ---
        # Quand on coche/décoche Dark
        self.chk_dark.toggled.connect(
            lambda v: parent._preview_theme(is_dark=v, color=self.cmb_color.currentText())
        )
        # Quand on change la couleur
        self.cmb_color.currentTextChanged.connect(
            lambda c: parent._preview_theme(is_dark=self.chk_dark.isChecked(), color=c)
        )

        # Boutons OK/Cancel
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

        # Si l'utilisateur ferme la boîte (Esc/Close) → même comportement qu'Annuler
        self.rejected.connect(self._restore_original_theme)

    def _restore_original_theme(self):
        parent: MainWindow = self.parent()  # type: ignore
        # réappliquer le thème initial (sans changer les prefs stockées)
        parent._apply_theme_values(self._orig_dark, self._orig_color)
        # remettre les libellés en cohérence avec l'état réel
        parent._update_theme_button_caption()

    def accept(self):
        # Commit des valeurs choisies
        parent: MainWindow = self.parent()  # type: ignore
        is_dark, color = self.values()
        # enregistrer dans la fenêtre + appliquer définitivement
        parent._is_dark = is_dark
        parent._theme_color = color
        parent._apply_theme()
        parent._update_theme_button_caption()
        parent.settings.setValue("ui/is_dark", parent._is_dark)
        parent.settings.setValue("ui/theme_color", parent._theme_color)
        parent._maybe_refresh(parent._tabs.currentIndex())
        super().accept()

    def reject(self):
        # Restaurer thème initial puis fermer
        self._restore_original_theme()
        super().reject()

    def values(self) -> tuple[bool, str]:
        return self.chk_dark.isChecked(), self.cmb_color.currentText()
