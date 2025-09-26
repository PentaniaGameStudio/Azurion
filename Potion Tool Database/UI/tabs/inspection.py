# ui_qt/tabs/inspection.py
from __future__ import annotations

from typing import List, Dict, Set, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QGroupBox, QGridLayout, QPushButton, QFrame, QScrollArea
)

from domain.rules import find_duplicates


class StatCard(QFrame):
    def __init__(self, title: str, value: int, parent=None):
        super().__init__(parent)
        self.setObjectName("StatCard")
        self.setFrameShape(QFrame.StyledPanel)
        self.setProperty("class", "card")

        lay = QVBoxLayout(self)
        self._title = QLabel(title)
        self._title.setProperty("class", "card-title")
        self._value = QLabel(str(value))
        self._value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._value.setProperty("class", "card-value")

        lay.addWidget(self._title)
        lay.addWidget(self._value)

    def set_value(self, v: int):
        self._value.setText(str(v))


class InspectionTab(QWidget):
    """
    Onglet Analyse :
    - 4 compteurs (Livres, Origines, Ingrédients, Recettes)
    - Livres sans ingrédients
    - Ingrédients non utilisés
    - Doublons : livres, ingrédients/recettes (IntegrityService), origines (dans un même ingrédient)
    """

    def __init__(self, container, parent=None):
        super().__init__(parent)
        self.container = container

        self.books_presenter = container["presenters"]["books"]
        self.ingredients_presenter = container["presenters"]["ingredients"]
        self.origins_presenter = container["presenters"]["origins"]
        self.inspection_presenter = container["presenters"]["inspection"]

        self.repos = container["repos"]
        self.services = container["services"]

        self._build_ui()
        self.refresh()

    # ---------- UI ----------

    def _build_ui(self):
        root = QVBoxLayout(self)

        # Stat cards
        self._card_books = StatCard("Livres", 0)
        self._card_origins = StatCard("Origines (nœuds)", 0)
        self._card_ingredients = StatCard("Ingrédients", 0)
        self._card_recipes = StatCard("Recettes", 0)

        cards = QHBoxLayout()
        cards.addWidget(self._card_books)
        cards.addWidget(self._card_origins)
        cards.addWidget(self._card_ingredients)
        cards.addWidget(self._card_recipes)
        root.addLayout(cards)

        # Scrollable lists area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        scroll.setWidget(container)
        grid = QGridLayout(container)

        # 1) Livres sans ingrédients
        self._list_books_unused = QListWidget()
        grid.addWidget(self._make_group("📚 Livres sans ingrédient", self._list_books_unused), 0, 0)

        # 2) Ingrédients non utilisés dans les recettes
        self._list_ing_unused = QListWidget()
        grid.addWidget(self._make_group("🥄 Ingrédients non utilisés", self._list_ing_unused), 0, 1)

        # 3) Doublons — Livres
        self._list_dup_books = QListWidget()
        grid.addWidget(self._make_group("➿ Doublons — Livres (BOOKS)", self._list_dup_books), 1, 0)

        # 4) Doublons — Noms (Ingrédients & Recettes)
        self._list_dup_names = QListWidget()
        grid.addWidget(self._make_group("➿ Doublons — Ingrédients & Recettes", self._list_dup_names), 1, 1)

        # 5) Doublons — Origines (dans un même ingrédient)
        self._list_dup_origins = QListWidget()
        grid.addWidget(self._make_group("➿ Doublons — Origines (dans un même ingrédient)", self._list_dup_origins), 2, 0, 1, 2)

        root.addWidget(scroll)

        # Bouton refresh manuel
        btns = QHBoxLayout()
        btn_refresh = QPushButton("Rafraîchir")
        btn_refresh.clicked.connect(self.refresh)
        btns.addStretch(1)
        btns.addWidget(btn_refresh)
        root.addLayout(btns)

        # Petites classes CSS pour le thème qt-material
        self.setStyleSheet("""
        #StatCard {
            border-radius: 12px;
            padding: 10px;
        }
        .card-title {
            font-size: 12pt;
            opacity: 0.8;
        }
        .card-value {
            font-size: 24pt;
            font-weight: 700;
        }
        QGroupBox {
            margin-top: 12px;
            font-weight: 600;
        }
        """)

    def _make_group(self, title: str, widget: QWidget):
        box = QGroupBox(title)
        lay = QVBoxLayout(box)
        lay.addWidget(widget)
        return box

    # ---------- Data refresh ----------

    def refresh(self):
        # Recalcule tout à partir des presenters/services
        books = list(self.repos["data"].get_books())
        origin_tree = self.repos["data"].get_origin_tree()
        ingredients = list(self.repos["ingredients"].list_all())
        recipes = list(self.repos["recipes"].list_all())

        # Compteurs
        nb_books = len(books)
        nb_origins = _count_nodes(origin_tree)  # tous les nœuds
        nb_ings = len(ingredients)
        nb_recs = len(recipes)

        self._card_books.set_value(nb_books)
        self._card_origins.set_value(nb_origins)
        self._card_ingredients.set_value(nb_ings)
        self._card_recipes.set_value(nb_recs)

        # Livres sans ingrédients (via BooksPresenter usages)
        table_vm = self.books_presenter.make_books_table()
        books_unused = [row.title for row in table_vm.rows if int(row.usage_count or 0) == 0]
        self._fill_list(self._list_books_unused, books_unused)

        # Ingrédients non utilisés (via IntegrityService)
        report = self.inspection_presenter.integrity.inspect()
        self._fill_list(self._list_ing_unused, report.unused_ingredients)

        # Doublons — Livres (BOOKS)
        dup_books = find_duplicates(books)
        self._fill_list(self._list_dup_books, dup_books)

        # Doublons — Noms (Ingrédients & Recettes)
        dup_names = sorted(set(report.duplicate_names))
        self._fill_list(self._list_dup_names, dup_names)

        # Doublons — Origines (dans un même ingrédient)
        dup_orig_pairs = _find_per_ingredient_origin_duplicates(ingredients)
        # Affichage sous forme "Ingrédient — /Chemin/Origine"
        dup_origin_items = [f"{ing} — {origin}" for ing, origin in dup_orig_pairs]
        self._fill_list(self._list_dup_origins, dup_origin_items)

    def _fill_list(self, widget: QListWidget, items: List[str]):
        widget.clear()
        if not items:
            it = QListWidgetItem("— Aucun —")
            it.setFlags(Qt.ItemIsEnabled)  # non sélectionnable
            widget.addItem(it)
            return
        for s in items:
            widget.addItem(QListWidgetItem(s))


# ---------- helpers ----------

def _count_nodes(tree: dict) -> int:
    """Compte tous les nœuds (parents + feuilles) d'un dict imbriqué."""
    if not isinstance(tree, dict) or not tree:
        return 0
    total = 0
    for _, children in tree.items():
        total += 1
        if isinstance(children, dict):
            total += _count_nodes(children)
    return total


def _find_per_ingredient_origin_duplicates(ingredients) -> List[tuple[str, str]]:
    """
    Retourne une liste de (ingredient_name, origin_path) lorsqu'une même origine
    apparaît plusieurs fois dans ing.origins. Utile pour 'doublon d'origine'.
    """
    out: List[tuple[str, str]] = []
    for ing in ingredients:
        seen: Set[str] = set()
        dups: Set[str] = set()
        for o in (ing.origins or []):
            if o in seen:
                dups.add(o)
            else:
                seen.add(o)
        for d in sorted(dups):
            out.append((ing.name, d))
    return out
