from __future__ import annotations
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QLineEdit, QLabel,
    QPushButton, QMessageBox, QInputDialog, QComboBox, QDialog, QDialogButtonBox
)

from domain.errors import PotionDBError


# ---------- helpers ----------
def info(self, text: str, title: str = "Info"):
    QMessageBox.information(self, title, text)

def warn(self, text: str, title: str = "Attention"):
    QMessageBox.warning(self, title, text)

def error(self, text: str, title: str = "Erreur"):
    QMessageBox.critical(self, title, text)


class MigrateOriginDialog(QDialog):
    """
    Choisir la cible de migration pour les références d'une origine (par libellé).
    new_name = ""  => suppression des références
    """
    def __init__(self, all_labels: List[str], source_label: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Migrer les références d'origine")
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel(f"Remplacer toutes les références à « {source_label} » par :"))
        self.cmb = QComboBox()
        choices = ["(Supprimer les références)"] + [l for l in sorted(all_labels) if l != source_label]
        self.cmb.addItems(choices)
        lay.addWidget(self.cmb)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def target_label(self) -> str:
        txt = self.cmb.currentText().strip()
        return "" if txt.startswith("(") else txt


# ---------- Onglet ----------
class OriginsTab(QWidget):
    def __init__(self, container, parent=None):
        super().__init__(parent)
        self.container = container
        self.presenters = container["presenters"]         # OriginsPresenter, IngredientsPresenter...
        self.repos = container["repos"]
        self.uc = container["use_cases"]["origins"]       # add / rename / remove / migrate_refs

        self._build_ui()
        self.refresh()

    # UI
    def _build_ui(self):
        root = QVBoxLayout(self)

        # Top bar
        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Rechercher une origine…")
        top.addWidget(self.search, 1)

        self.btn_add_child = QPushButton("Ajouter enfant")
        self.btn_rename    = QPushButton("Renommer")
        self.btn_migrate   = QPushButton("Migrer références")
        self.btn_delete    = QPushButton("Supprimer")

        for b in (self.btn_add_child, self.btn_rename, self.btn_migrate, self.btn_delete):
            top.addWidget(b)

        root.addLayout(top)

        # Tree (compact, sans flèches visibles)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(14)
        self.tree.setUniformRowHeights(True)
        self.tree.setRootIsDecorated(True) 
        self.tree.setStyleSheet("""
            QTreeWidget { padding: 4px; }
            QTreeWidget::item { padding: 2px 6px; }
        """)
        root.addWidget(self.tree, 1)
        self.tree.setAnimated(True)                  # petite animation d’ouverture
        self.tree.setItemsExpandable(True)           # chaque item peut s’ouvrir/se fermer

        # interactions
        self.search.textChanged.connect(self._filter_tree)
        self.tree.itemDoubleClicked.connect(lambda *_: self._rename_selected())
        self.btn_add_child.clicked.connect(self._add_child)
        self.btn_rename.clicked.connect(self._rename_selected)
        self.btn_migrate.clicked.connect(self._migrate_selected)
        self.btn_delete.clicked.connect(self._delete_selected)

    # Data
    def refresh(self):
        self._tree_dict = self.presenters["origins"].get_origin_tree()
        self._all_labels = self._collect_labels(self._tree_dict)
        self._rebuild_tree()
        self._filter_tree()  # applique filtre courant (vide au départ)

    def _rebuild_tree(self):
        self.tree.clear()
        def add_children(node: dict, parent_item: Optional[QTreeWidgetItem], prefix: str):
            for label, children in (node or {}).items():
                path = f"{prefix}/{label}" if prefix else label
                item = QTreeWidgetItem([label])  # affichage du dernier nom uniquement
                item.setData(0, Qt.UserRole, path)  # on garde le chemin complet pour les use-cases
                if parent_item is None:
                    self.tree.addTopLevelItem(item)
                else:
                    parent_item.addChild(item)
                if isinstance(children, dict) and children:
                    add_children(children, item, path)

        add_children(self._tree_dict, None, "")
        self.tree.expandAll()

    def _filter_tree(self):
        q = (self.search.text() or "").strip().lower()
        def visit(item: QTreeWidgetItem) -> bool:
            # visible si lui ou un descendant match
            text = (item.text(0) or "").lower()
            visible_here = (q in text) if q else True
            visible_child = False
            for i in range(item.childCount()):
                if visit(item.child(i)):
                    visible_child = True
            visible = visible_here or visible_child
            item.setHidden(not visible)
            return visible
        for i in range(self.tree.topLevelItemCount()):
            visit(self.tree.topLevelItem(i))

    # Utils
    def _selected_item(self) -> Optional[QTreeWidgetItem]:
        items = self.tree.selectedItems()
        return items[0] if items else None

    def _selected_path(self) -> str:
        it = self._selected_item()
        return (it.data(0, Qt.UserRole) or "") if it else ""

    def _selected_label(self) -> str:
        path = self._selected_path()
        return path.split("/")[-1] if path else ""

    def _collect_labels(self, node: dict) -> List[str]:
        out: List[str] = []
        def walk(n: dict):
            for k, v in (n or {}).items():
                out.append(str(k))
                if isinstance(v, dict) and v:
                    walk(v)
        walk(node or {})
        return sorted(set(out))

    # Actions
    def _add_child(self):
        parent_path = self._selected_path()
        if parent_path == "":
            # autoriser l’ajout à la racine
            parent_path = ""  # AddOrigin accepte "" => racine
        name, ok = QInputDialog.getText(self, "Ajouter un enfant", "Nom du nouveau nœud :")
        name = (name or "").strip()
        if not ok or not name:
            return
        try:
            self.uc["add"].execute(parent_path, name)
            info(self, f"Enfant « {name} » créé.")
            self.refresh()
            self._select_path(f"{parent_path}/{name}".strip("/"))
        except PotionDBError as e:
            error(self, str(e))

    def _rename_selected(self):
        old_path = self._selected_path()
        if not old_path:
            warn(self, "Sélectionnez un nœud à renommer.")
            return
        old_label = old_path.split("/")[-1]
        new_name, ok = QInputDialog.getText(self, "Renommer l'origine", "Nouveau nom :", text=old_label)
        new_name = (new_name or "").strip()
        if not ok or not new_name or new_name == old_label:
            return
        try:
            # 1) renommer le nœud dans l’arbre (chemin complet)
            self.uc["rename"].execute(old_path, new_name)
            # 2) migrer les références (dans les ingrédients) par LIBELLÉ (dernier segment)
            self.uc["migrate_refs"].execute(old_path=old_label, new_name=new_name)
            info(self, f"Renommé en « {new_name} » et références actualisées.")
            self.refresh()
            # re-sélectionner le nouveau chemin
            parent = "/".join([p for p in old_path.split("/") if p][:-1])
            self._select_path(f"{parent}/{new_name}".strip("/"))
        except PotionDBError as e:
            error(self, str(e))

    def _migrate_selected(self):
        src_label = self._selected_label()
        if not src_label:
            warn(self, "Sélectionnez une origine à migrer.")
            return
        dlg = MigrateOriginDialog(self._all_labels, src_label, self)
        if dlg.exec() != QDialog.Accepted:
            return
        dst_label = dlg.target_label()  # "" => suppression des références
        if dst_label == src_label:
            warn(self, "La cible doit être différente de la source.")
            return
        try:
            self.uc["migrate_refs"].execute(old_path=src_label, new_name=dst_label)
            if dst_label:
                info(self, f"Références migrées : « {src_label} » → « {dst_label} »")
            else:
                info(self, f"Références à « {src_label} » supprimées.")
        except PotionDBError as e:
            error(self, str(e))

    def _delete_selected(self):
        path = self._selected_path()
        if not path:
            return
        label = path.split("/")[-1]
        reply = QMessageBox.question(
            self, "Supprimer ce nœud",
            f"Supprimer « {label} » de l'arbre ?\n"
            f"(Les références dans les ingrédients seront retirées.)",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            # 1) retirer le nœud de l’arbre
            self.uc["remove"].execute(path)
            # 2) supprimer les références par LIBELLÉ
            self.uc["migrate_refs"].execute(old_path=label, new_name="")
            info(self, "Nœud supprimé et références nettoyées.")
            self.refresh()
        except PotionDBError as e:
            error(self, str(e))

    def _select_path(self, path: str):
        # sélectionne l’item correspondant au chemin complet stocké dans UserRole
        for i in range(self.tree.topLevelItemCount()):
            it = self.tree.topLevelItem(i)
            found = self._select_path_rec(it, path)
            if found:
                break

    def _select_path_rec(self, it: QTreeWidgetItem, path: str) -> bool:
        if (it.data(0, Qt.UserRole) or "") == path:
            self.tree.setCurrentItem(it)
            return True
        for i in range(it.childCount()):
            if self._select_path_rec(it.child(i), path):
                return True
        return False
