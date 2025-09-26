from __future__ import annotations
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
    QListWidget, QListWidgetItem, QLineEdit, QLabel,
    QPushButton, QToolButton, QDialog, QDialogButtonBox,
    QMessageBox, QSplitter, QComboBox, QInputDialog
)

from domain.errors import PotionDBError, DuplicateNameError, ValidationError


# ---------- helpers ----------

def info(self, text: str, title: str = "Info"):
    QMessageBox.information(self, title, text)

def warn(self, text: str, title: str = "Attention"):
    QMessageBox.warning(self, title, text)

def error(self, text: str, title: str = "Erreur"):
    QMessageBox.critical(self, title, text)


class DeletableList(QListWidget):
    """
    QListWidget multi-sélection avec suppression via 'Del' et double-clic callback.
    """
    def __init__(self, on_delete_callback=None, on_activate_callback=None, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QListWidget.ExtendedSelection)
        self._on_delete = on_delete_callback
        if on_activate_callback:
            self.itemDoubleClicked.connect(lambda _: on_activate_callback())

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            if self._on_delete:
                self._on_delete()
            e.accept()
            return
        super().keyPressEvent(e)


class MigrateDialog(QDialog):
    """
    Choix d'une cible pour migrer les références d'un livre.
    """
    def __init__(self, books: List[str], source_title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Migrer les références")
        lay = QVBoxLayout(self)

        lay.addWidget(QLabel(f"Remplacer toutes les références à:\n« {source_title} »\npar:"))
        self.cmb = QComboBox()
        self.cmb.addItems([b for b in books if b != source_title])
        lay.addWidget(self.cmb)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def target(self) -> Optional[str]:
        return self.cmb.currentText().strip() if self.cmb.count() > 0 else None


# ---------- Onglet Livres ----------

class BooksTab(QWidget):
    def __init__(self, container, parent=None):
        super().__init__(parent)
        self.container = container
        self.presenters = container["presenters"]
        self.repos = container["repos"]
        self.uc_books = container["use_cases"]["books"]     # add/rename/remove/migrate

        self._build_ui()
        self.refresh()

    # --- UI ---

    def _build_ui(self):
        root = QVBoxLayout(self)

        # barre du haut: recherche + boutons
        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Rechercher / Saisir un titre pour Ajouter…")
        top.addWidget(self.search, 1)

        self.btn_add = QPushButton("Ajouter")
        self.btn_rename = QPushButton("Renommer")
        self.btn_delete = QPushButton("Supprimer")
        self.btn_migrate = QPushButton("Migrer références")

        self.btn_add.clicked.connect(self._add_from_search)
        self.btn_rename.clicked.connect(self._rename_selected)
        self.btn_delete.clicked.connect(self._delete_selected)
        self.btn_migrate.clicked.connect(self._migrate_selected)

        for b in (self.btn_add, self.btn_rename, self.btn_delete, self.btn_migrate):
            top.addWidget(b)

        root.addLayout(top)

        # liste
        self.list = DeletableList(self._delete_selected, self._rename_selected)
        root.addWidget(self.list, 1)

        # interactions
        self.search.textChanged.connect(self._refresh_list)

        # style léger
        self.setStyleSheet("QListWidget { min-height: 220px; }")

    # --- Data ---

    def refresh(self):
        self._all_rows = self.presenters["books"].make_books_table().rows  # BookRowVM[]
        self._refresh_list()

    def _refresh_list(self):
        q = (self.search.text() or "").strip().lower()
        self.list.clear()
        for row in self._all_rows:
            if q and q not in row.title.lower():
                continue
            text = f"{row.title} — {row.usage_count} ingrédient(s)"
            it = QListWidgetItem(text)
            it.setData(Qt.UserRole, row.title)
            self.list.addItem(it)

    def _selected_titles(self) -> List[str]:
        return [it.data(Qt.UserRole) for it in self.list.selectedItems() if it.data(Qt.UserRole)]

    # --- Actions ---

    def _add_from_search(self):
        title = (self.search.text() or "").strip()
        if not title:
            warn(self, "Saisissez un titre dans le champ de recherche pour ajouter.")
            return
        try:
            self.uc_books["add"].execute(title)
            info(self, f"Livre « {title} » ajouté.")
            self.search.clear()
            self.refresh()
        except PotionDBError as e:
            error(self, str(e))

    def _rename_selected(self):
        titles = self._selected_titles()
        if not titles:
            warn(self, "Sélectionnez un livre à renommer.")
            return
        if len(titles) > 1:
            warn(self, "Renommez un seul livre à la fois.")
            return
        old = titles[0]
        new, ok = QInputDialog.getText(self, "Renommer le livre", "Nouveau titre:", text=old)
        new = (new or "").strip()
        if not ok or not new or new == old:
            return
        try:
            # 1) renomme dans BOOKS
            self.uc_books["rename"].execute(old, new)
            # 2) migre toutes les références d’ingrédients de old -> new
            self.uc_books["migrate_refs"].execute(old_title=old, new_title=new)
            info(self, f"Renommé en « {new} » et références migrées.")
            self.refresh()
            # re-sélection
            self._select_in_list(new)
        except PotionDBError as e:
            error(self, str(e))

    def _delete_selected(self):
        titles = self._selected_titles()
        if not titles:
            return
        reply = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Supprimer {len(titles)} livre(s) sélectionné(s) ?\n"
            "Les références résiduelles seront nettoyées.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            for t in titles:
                self.uc_books["remove"].execute(t)
            info(self, "Suppression effectuée.")
            self.refresh()
        except PotionDBError as e:
            error(self, str(e))

    def _migrate_selected(self):
        titles = self._selected_titles()
        if not titles:
            warn(self, "Sélectionnez un livre source.")
            return
        if len(titles) > 1:
            warn(self, "Migration: sélectionnez un seul livre source.")
            return
        src = titles[0]
        books = [r.title for r in self._all_rows]
        dlg = MigrateDialog(books, src, self)
        if dlg.exec() != QDialog.Accepted:
            return
        dst = dlg.target()
        if not dst:
            warn(self, "Aucune cible choisie.")
            return
        if dst == src:
            warn(self, "La cible doit être différente de la source.")
            return
        try:
            self.uc_books["migrate_refs"].execute(old_title=src, new_title=dst)
            info(self, f"Références migrées: « {src} » → « {dst} »")
            self.refresh()
            self._select_in_list(dst)
        except PotionDBError as e:
            error(self, str(e))

    def _select_in_list(self, title: str):
        for i in range(self.list.count()):
            it = self.list.item(i)
            if it.data(Qt.UserRole) == title:
                self.list.setCurrentItem(it)
                break
