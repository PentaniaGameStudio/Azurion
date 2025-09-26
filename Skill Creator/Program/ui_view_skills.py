# -*- coding: utf-8 -*-
"""View tab listing skills and displaying their details."""
from __future__ import annotations

import json
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QSplitter,
    QTextEdit,
    QMessageBox,
    QFileDialog,
)

from .datastore import DataStore
from .models import Skill


class ViewSkillsTab(QWidget):
    """List of skills with a detail pane."""

    COLUMNS = ("family", "name", "level")

    def __init__(self, store: DataStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.store = store

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel("Afficher les Compétences")
        header.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(header)

        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("Rechercher:"))
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("Nom, famille, coût, effet…")
        self.search_entry.returnPressed.connect(self.refresh)
        top_row.addWidget(self.search_entry, 1)
        refresh_btn = QPushButton("Actualiser")
        refresh_btn.clicked.connect(self.refresh)
        top_row.addWidget(refresh_btn)
        layout.addLayout(top_row)

        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter, 1)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Famille", "Nom", "Niv"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QTreeWidget.SingleSelection)
        self.tree.itemSelectionChanged.connect(self._on_select)
        self.tree.setRootIsDecorated(False)
        left_layout.addWidget(self.tree, 1)

        splitter.addWidget(left_widget)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        self.detail_title = QLabel("Aucune compétence sélectionnée")
        self.detail_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        right_layout.addWidget(self.detail_title)

        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        right_layout.addWidget(self.detail_text, 1)

        btn_row = QHBoxLayout()
        delete_btn = QPushButton("Supprimer")
        delete_btn.clicked.connect(self._delete_selected)
        btn_row.addWidget(delete_btn)

        export_btn = QPushButton("Exporter la sélection (JSON)")
        export_btn.clicked.connect(self._export_selected)
        btn_row.addWidget(export_btn)
        btn_row.addStretch(1)
        right_layout.addLayout(btn_row)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        self.refresh()

    def set_store(self, store: DataStore) -> None:
        self.store = store
        self.refresh()

    def refresh(self) -> None:
        query = self.search_entry.text().strip().lower()

        self.tree.clear()

        lvl_order_map = {"niv1": 1, "niv2": 2, "niv3": 3}
        rows = []
        for idx, skill in enumerate(self.store.skills):
            family = skill.family
            name = skill.name
            level = getattr(skill, "level", "") or ""
            order_level = lvl_order_map.get(level.lower(), 999)
            searchable_parts = [
                family,
                name,
                level,
                getattr(skill, "cost", "") or "",
                getattr(skill, "difficulty", "") or "",
                getattr(skill, "target", "") or "",
                getattr(skill, "range_", "") or "",
                getattr(skill, "duration", "") or "",
                getattr(skill, "damage", "") or "",
                " ".join(getattr(skill, "effects", []) or []),
                " ".join(getattr(skill, "conditions", []) or []),
                " ".join(getattr(skill, "limits", []) or []),
            ]
            searchable = " ".join(searchable_parts).lower()
            if query and query not in searchable:
                continue
            rows.append(((family, order_level, name.lower()), idx, (family, name, level)))

        rows.sort(key=lambda item: item[0])

        for _key, idx, values in rows:
            item = QTreeWidgetItem(list(values))
            item.setData(0, Qt.UserRole, idx)
            self.tree.addTopLevelItem(item)

        self.detail_title.setText("Aucune compétence sélectionnée")
        self.detail_text.setPlainText("Sélectionnez une compétence dans la liste pour voir ses détails.")

    def _on_select(self) -> None:
        items = self.tree.selectedItems()
        if not items:
            self._set_detail(None)
            return
        idx = items[0].data(0, Qt.UserRole)
        if idx is None:
            self._set_detail(None)
            return
        self._set_detail(self.store.skills[int(idx)])

    def _set_detail(self, skill: Optional[Skill]) -> None:
        if skill is None:
            self.detail_title.setText("Aucune compétence sélectionnée")
            self.detail_text.setPlainText("Sélectionnez une compétence dans la liste pour voir ses détails.")
            return

        self.detail_title.setText(f"{skill.family}  {skill.name}")

        family = getattr(skill, "family", "") or ""
        name = getattr(skill, "name", "") or ""
        level = getattr(skill, "level", "") or ""
        cost = getattr(skill, "cost", "") or ""
        diff = getattr(skill, "difficulty", "") or ""
        if diff.strip() == "Difficulté : 0":
            diff = ""
        target = getattr(skill, "target", "") or ""
        range_ = getattr(skill, "range_", "") or ""
        duration = getattr(skill, "duration", "") or ""
        damage = getattr(skill, "damage", "") or ""

        def _norm_list(values):
            return [x.strip() for x in (values or []) if isinstance(x, str) and x.strip()]

        effects = _norm_list(getattr(skill, "effects", []))
        conditions = _norm_list(getattr(skill, "conditions", []))
        limits = _norm_list(getattr(skill, "limits", []))

        lines: list[str] = []
        header = f"{family} {name}"
        if level:
            header += f" ({level})"
        lines.append(header)

        if cost:
            lines.append(f"\tCoût : {cost}")
        if diff:
            lines.append(f"\t{diff}")
        if target:
            lines.append(f"\tCible : {target}")
        if range_:
            lines.append(f"\tPortée : {range_}")
        if duration:
            lines.append(f"\tDurée : {duration}")
        if damage:
            lines.append(f"\tDégâts : {damage}")

        if len(effects) == 1:
            lines.append(f"\tEffet : {effects[0]}")
        elif len(effects) > 1:
            lines.append("\tEffets :")
            for eff in effects:
                lines.append(f"\t\t{eff}")

        if len(conditions) == 1:
            lines.append(f"\tCondition : {conditions[0]}")
        elif len(conditions) > 1:
            lines.append("\tConditions :")
            for cond in conditions:
                lines.append(f"\t\t{cond}")

        if len(limits) == 1:
            lines.append(f"\tLimite : {limits[0]}")
        elif len(limits) > 1:
            lines.append("\tLimites :")
            for lim in limits:
                lines.append(f"\t\t{lim}")

        self.detail_text.setPlainText("\n".join(lines))

    def _selected_index(self) -> Optional[int]:
        items = self.tree.selectedItems()
        if not items:
            return None
        idx = items[0].data(0, Qt.UserRole)
        return int(idx) if idx is not None else None

    def _delete_selected(self) -> None:
        idx = self._selected_index()
        if idx is None:
            QMessageBox.information(self, "Info", "Aucune compétence sélectionnée.")
            return
        skill = self.store.skills[idx]
        if QMessageBox.question(
            self,
            "Confirmation",
            f"Supprimer '{skill.name}' ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        ) != QMessageBox.Yes:
            return
        del self.store.skills[idx]
        self.store.save()
        self.refresh()

    def _export_selected(self) -> None:
        idx = self._selected_index()
        if idx is None:
            QMessageBox.information(self, "Info", "Aucune compétence sélectionnée.")
            return
        skill = self.store.skills[idx]
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter la compétence en JSON",
            f"{skill.name.replace(' ', '_')}.json",
            "JSON files (*.json)",
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(skill.__dict__, fh, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "Exporté", f"Compétence exportée vers:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Erreur", f"Export impossible:\n{exc}")
