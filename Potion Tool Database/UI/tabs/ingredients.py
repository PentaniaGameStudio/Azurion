from __future__ import annotations
from typing import List, Optional, Tuple

from PySide6.QtCore import Qt, QSize, QTimer, Signal
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
    QListWidget, QListWidgetItem, QListView, QLineEdit, QLabel,
    QPushButton, QToolButton, QFrame, QGroupBox, QComboBox,
    QTextEdit, QMessageBox, QSplitter, QMenu, QCheckBox, QWidgetAction,
    QSizePolicy
)

from domain.errors import PotionDBError, ValidationError, DuplicateNameError


# ---------- Small helpers ----------

def info(self, text: str, title: str = "Info"):
    QMessageBox.information(self, title, text)

def warn(self, text: str, title: str = "Attention"):
    QMessageBox.warning(self, title, text)

def error(self, text: str, title: str = "Erreur"):
    QMessageBox.critical(self, title, text)


class DeletableList(QListWidget):
    """
    QListWidget multi-sélection avec suppression via 'Del'.
    """
    def __init__(self, on_delete_callback, on_activate_callback, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QListWidget.ExtendedSelection)
        self._on_delete = on_delete_callback
        self.itemDoubleClicked.connect(lambda _: on_activate_callback())

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            if self._on_delete:
                self._on_delete()
            e.accept()
            return
        super().keyPressEvent(e)


class CategoryToggle(QFrame):
    """
    3 toggles exclusifs : 💧 Liant / ⚗️ Catalyseur / 🧬 Réactif
    """
    changed = Signal()  # ///summary: émis quand la catégorie change (UI)

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0,0,0,0)

        self.btn_liant = QToolButton(text="💧 Liant", checkable=True, autoExclusive=True)
        self.btn_cata  = QToolButton(text="⚗️ Catalyseur", checkable=True, autoExclusive=True)
        self.btn_reac  = QToolButton(text="🧬 Réactif", checkable=True, autoExclusive=True)

        for b in (self.btn_liant, self.btn_cata, self.btn_reac):
            b.setToolButtonStyle(Qt.ToolButtonTextOnly)
            # ///summary: n'émet que sur True pour éviter deux événements
            b.toggled.connect(lambda ch, b=b: (ch and self.changed.emit()))
            lay.addWidget(b)

        # le conteneur lui-même ne s’étire pas
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def set_value(self, cat: str):
        v = (cat or "").strip().lower()
        self.btn_liant.setChecked(v == "liant" or v == "💧 liant")
        self.btn_cata.setChecked(v == "catalyseur" or "catalyst" in v)
        self.btn_reac.setChecked(v == "réactif" or v == "reactif")

    def get_value(self) -> str:
        if self.btn_liant.isChecked():
            return "Liant"
        if self.btn_cata.isChecked():
            return "Catalyseur"
        if self.btn_reac.isChecked():
            return "Réactif"
        return ""


class BooksChecklist(QListWidget):
    """
    Liste de livres avec de vrais QCheckBox, en *deux rangées* (flow LTR + wrap).
    """
    changed = Signal()  # ///summary: émis quand une coche livre change

    def __init__(self, books: List[str], parent=None):
        super().__init__(parent)
        # Vue en mode icônes pour activer Flow + Wrapping
        self.setViewMode(QListView.IconMode)
        self.setFlow(QListView.LeftToRight)
        self.setWrapping(True)
        self.setResizeMode(QListView.Adjust)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setUniformItemSizes(True)

        # taille d'une "tuile" livre (largeur ~ 300px, hauteur ~ 40px)
        self._tile_size = QSize(300, 40)
        self.setGridSize(self._tile_size)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)

        self.setSelectionMode(QListWidget.NoSelection)
        self.setAlternatingRowColors(False)
        self.populate(books)

        self.setStyleSheet("""
            QListWidget { padding: 2px; }
            QListWidget::item { margin: 2px; }
            QCheckBox { font-size: 14px; padding: 0px; }
        """)

    def _emit_changed(self, *_):
        self.changed.emit()

    def populate(self, books: List[str]):
        self.clear()
        for title in books:
            item = QListWidgetItem(self)
            item.setSizeHint(self._tile_size)
            cb = QCheckBox(title)
            cb.setProperty("book_title", title)
            cb.toggled.connect(self._emit_changed)  # ///summary: autosave hook
            self.setItemWidget(item, cb)

    def set_checked(self, selected: List[str]):
        wanted = set(selected or [])
        for i in range(self.count()):
            cb: QCheckBox = self.itemWidget(self.item(i))
            if cb:
                cb.blockSignals(True)
                cb.setChecked(cb.text() in wanted)
                cb.blockSignals(False)

    def get_checked(self) -> List[str]:
        out: List[str] = []
        for i in range(self.count()):
            cb: QCheckBox = self.itemWidget(self.item(i))
            if cb and cb.isChecked():
                out.append(cb.text())
        return out


class OriginList(QListWidget):
    """
    Liste aplatie de l'arbre des origines avec de vrais QCheckBox.
    - Tous les niveaux sont cochables (parents + feuilles)
    - Hiérarchie rendue par indentation (espaces)
    - Mode multi (par défaut) ou mono (utilisé par le filtre)
    """
    changed = Signal()  # ///summary: émis à tout toggle

    def __init__(self, tree: dict, *, multi: bool, parent=None):
        super().__init__(parent)
        self.tree = tree or {}
        self.multi = multi
        self.setSelectionMode(QListWidget.NoSelection)
        self.setUniformItemSizes(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.rebuild()
        self.setStyleSheet("QListWidget::item { padding: 0px 0px; font-size: 12px; }")

    def rebuild(self):
        self.clear()
        def walk(node: dict, prefix: str, depth: int):
            for label, children in (node or {}).items():
                path = f"{prefix}/{label}" if prefix else label
                item = QListWidgetItem(self)
                item.setSizeHint(QSize(26, 22))  # un peu plus compact

                cb = QCheckBox(label)  # <-- plus d'espaces dans le libellé
                cb.setProperty("origin_path", path)

                # décalage réel du checkbox (icône + texte) selon la profondeur
                indent_px = 14 * depth
                cb.setStyleSheet(f"QCheckBox {{ margin-left: {indent_px}px; font-size: 11px; padding: 0px; }}")

                if self.multi:
                    cb.toggled.connect(lambda _ch: self.changed.emit())
                else:
                    cb.toggled.connect(self._on_toggle)

                self.setItemWidget(item, cb)

                if isinstance(children, dict) and children:
                    walk(children, path, depth + 1)

        walk(self.tree, "", 0)

    def _on_toggle(self, checked: bool):
        if not checked:
            self.changed.emit()
            return
        sender: QCheckBox = self.sender()  # type: ignore
        for i in range(self.count()):
            cb: QCheckBox = self.itemWidget(self.item(i))
            if cb is not None and cb is not sender and cb.isChecked():
                cb.blockSignals(True)
                cb.setChecked(False)
                cb.blockSignals(False)
        self.changed.emit()

    def set_checked_paths(self, paths: list[str]):
        """Accepte chemins complets ET labels courts."""
        wanted = set(paths or [])
        wanted_last = {p.split("/")[-1] for p in wanted}
        for i in range(self.count()):
            cb: QCheckBox = self.itemWidget(self.item(i))
            if not cb:
                continue
            path = cb.property("origin_path")
            last = str(path).split("/")[-1] if path else ""
            cb.blockSignals(True)
            cb.setChecked(path in wanted or last in wanted_last)
            cb.blockSignals(False)

    def get_checked_paths(self) -> List[str]:
        out: List[str] = []
        for i in range(self.count()):
            cb: QCheckBox = self.itemWidget(self.item(i))
            if cb and cb.isChecked():
                path = cb.property("origin_path")
                if path:
                    out.append(path)
        # unique en gardant l'ordre
        seen = set()
        uniq = []
        for p in out:
            if p not in seen:
                seen.add(p)
                uniq.append(p)
        return uniq

    def set_tree(self, tree: dict):
        self.tree = tree or {}
        self.rebuild()


class OriginFilterButton(QToolButton):
    def __init__(self, tree: dict, parent=None):
        super().__init__(parent)
        self.setText("Origine (toutes)")
        self.setPopupMode(QToolButton.InstantPopup)

        self._menu = QMenu(self)
        self.setMenu(self._menu)

        # contenu du menu avec parents corrects
        content = QWidget(self._menu)
        lay = QVBoxLayout(content)
        lay.setContentsMargins(6, 6, 6, 6)

        self._list = OriginList(tree, multi=False, parent=content)
        lay.addWidget(self._list)

        btn_clear = QPushButton("Aucune", parent=content)
        btn_clear.clicked.connect(self.clear_selection)
        lay.addWidget(btn_clear)

        wact = QWidgetAction(self._menu)
        wact.setDefaultWidget(content)
        self._menu.addAction(wact)

        self._menu.setStyleSheet("QMenu { margin: 4px; }")
        self._menu.setMinimumWidth(280)
        self._menu.setMinimumHeight(360)
        self._menu.aboutToHide.connect(self._sync_caption)

    def clear_selection(self):
        self._list.set_checked_paths([])
        self.setText("Origine (toutes)")

    def set_selected_path(self, path: Optional[str]):
        self._list.set_checked_paths([path] if path else [])
        self._sync_caption()

    def selected_label(self) -> Optional[str]:
        paths = self._list.get_checked_paths()
        if not paths:
            return None
        return paths[0].split("/")[-1]

    def set_tree(self, tree: dict):
        self._list.set_tree(tree)
        self._sync_caption()

    def _sync_caption(self):
        label = self.selected_label()
        self.setText(label if label else "Origine (toutes)")


# ---------- Main tab ----------

class IngredientsTab(QWidget):
    def __init__(self, container, parent=None):
        super().__init__(parent)
        self.container = container
        self.presenters = container["presenters"]
        self.repos = container["repos"]
        self.uc = container["use_cases"]["ingredients"]

        self._current_original_name: Optional[str] = None  # pour gérer rename
        self._is_loading = False                            # ///summary: évite autosave pendant chargements
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.setInterval(300)               # ///summary: debounce autosave 300ms
        self._autosave_timer.timeout.connect(lambda: self._save(autosave=True))

        self._build_ui()
        self._wire_autosave()  # ///summary: branche les signaux utilisateurs -> autosave
        self.refresh()

    def _cat_emoji(self, cat: str) -> str:
        m = {
            "Liant": "💧",
            "Catalyseur": "⚗️",
            "Réactif": "🧬",
        }
        return m.get((cat or "").strip(), "")

    # ---- UI ----

    def _build_ui(self):
        root = QHBoxLayout(self)

        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter)

        # LEFT: list + filters
        left = QWidget()
        left_lay = QVBoxLayout(left)

        topbar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Rechercher...")
        btn_filter = QToolButton(text="Filtres")
        btn_filter.setCheckable(True)
        btn_filter.setChecked(False)
        btn_filter.toggled.connect(self._toggle_filters)
        topbar.addWidget(self.search, 1)
        topbar.addWidget(btn_filter, 0)
        left_lay.addLayout(topbar)

        # Filters (hidden by default)
        self.filters = QFrame()
        self.filters.setVisible(False)
        fl = QHBoxLayout(self.filters)
        self.cmb_cat = QComboBox()
        self.cmb_cat.addItem("(Toutes)")
        self.cmb_book = QComboBox()
        self.cmb_book.addItem("(Tous)")
        # Origin filter button (single selection among leaves)
        self._origin_filter_btn = OriginFilterButton(self.repos["data"].get_origin_tree())

        fl.addWidget(QLabel("Catégorie:"))
        fl.addWidget(self.cmb_cat, 1)
        fl.addWidget(QLabel("Livre:"))
        fl.addWidget(self.cmb_book, 1)
        fl.addWidget(self._origin_filter_btn, 0)
        left_lay.addWidget(self.filters)

        # List
        self.list = DeletableList(self._delete_selected, self._activate_selected)
        left_lay.addWidget(self.list, 1)

        splitter.addWidget(left)

        # RIGHT: editor area with inner splitter (form | origins panel)
        right_splitter = QSplitter(Qt.Horizontal)

        # --- Form panel (name, cat, diff, short, effect, books)
        form_panel = QWidget()
        form = QGridLayout(form_panel)
        row = 0

        self.ed_name = QLineEdit()
        form.addWidget(QLabel("Nom"), row, 0)
        form.addWidget(self.ed_name, row, 1)
        row += 1

        self.cat_toggle = CategoryToggle()
        form.addWidget(QLabel("Catégorie"), row, 0)
        form.addWidget(self.cat_toggle, row, 1, alignment=Qt.AlignCenter)
        row += 1

        self.ed_diff = QLineEdit()
        self.ed_diff.setPlaceholderText("Entier (peut être négatif)")
        form.addWidget(QLabel("Difficulté"), row, 0)
        form.addWidget(self.ed_diff, row, 1)
        row += 1

        self.ed_short = QLineEdit()
        form.addWidget(QLabel("Résumé"), row, 0)
        form.addWidget(self.ed_short, row, 1)
        row += 1

        self.ed_effect = QTextEdit()
        self.ed_effect.setObjectName("EffectEdit")
        self.ed_effect.setFrameStyle(QFrame.NoFrame)
        # Limiter la hauteur à ~2 lignes
        fm = self.ed_effect.fontMetrics()
        self.ed_effect.setFixedHeight((fm.lineSpacing() + 7) * 3)
        form.addWidget(QLabel("Effet détaillé"), row, 0)
        form.addWidget(self.ed_effect, row, 1)
        row += 1

        # Books (2 rangées)
        self.books_check = BooksChecklist(self.repos["data"].get_books())
        form.addWidget(QLabel("Livres"), row, 0)
        form.addWidget(self.books_check, row, 1)
        row += 1

        form.setColumnStretch(0, 0)
        form.setColumnStretch(1, 1)
        # Repartition verticale (à placer après avoir rempli la grille)
        form.setRowStretch(0, 0)  # Nom
        form.setRowStretch(1, 0)  # Catégorie
        form.setRowStretch(2, 0)  # Difficulté
        form.setRowStretch(3, 0)  # Résumé
        form.setRowStretch(4, 1)  # Effet détaillé (3 lignes mais peut respirer)
        form.setRowStretch(5, 6)  # Livres (on lui donne plus de place)
        form.setRowStretch(6, 1)  # Origines (un peu moins que Livres)

        # CRUD buttons under form
        btns = QHBoxLayout()
        self.btn_new = QPushButton("Nouveau")
        self.btn_dup = QPushButton("Dupliquer")
        self.btn_save = QPushButton("Enregistrer")
        self.btn_del = QPushButton("Supprimer")

        self.btn_new.clicked.connect(self._new)
        self.btn_dup.clicked.connect(self._duplicate_current)
        self.btn_save.clicked.connect(lambda: self._save(autosave=False))
        self.btn_del.clicked.connect(self._delete_current)

        btns.addStretch(1)  # ///summary: centrer les boutons (stretch gauche)
        for b in (self.btn_new, self.btn_dup, self.btn_save, self.btn_del):
            btns.addWidget(b)
        btns.addStretch(1)  # ///summary: centrer les boutons (stretch droite)

        form_box = QVBoxLayout()
        form_box.addWidget(form_panel, 1)
        form_box.addLayout(btns, 0)
        form_wrap = QWidget()
        form_wrap.setLayout(form_box)

        # --- Origins vertical panel (juxtaposé)
        origins_panel = QWidget()
        origins_lay = QVBoxLayout(origins_panel)
        origins_lay.addWidget(QLabel("Origines"))
        self.origins_tree = OriginList(self.repos["data"].get_origin_tree(), multi=True)
        origins_lay.addWidget(self.origins_tree, 1)

        right_splitter.addWidget(form_wrap)
        right_splitter.addWidget(origins_panel)
        right_splitter.setStretchFactor(0, 10)  # form plus large
        right_splitter.setStretchFactor(1, 1)   # origines prennent de la place verticale

        splitter.addWidget(right_splitter)
        splitter.setStretchFactor(0, 3) # liste
        splitter.setStretchFactor(1, 2) # panneau de droite

        # Interactions
        self.search.textChanged.connect(self._refresh_list)
        self.cmb_cat.currentIndexChanged.connect(self._refresh_list)
        self.cmb_book.currentIndexChanged.connect(self._refresh_list)

        form_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        form_wrap.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # style léger
        self.setStyleSheet("""
        QListWidget { min-height: 140px; }

        /* Effet détaillé : pas de bord en idle, léger au survol, bleu au focus */
        #EffectEdit {
            border: 1px solid transparent;
            border-radius: 6px;
            padding: 6px;
        }
        #EffectEdit:hover {
            border: 1px solid rgba(77,163,255,0.35);
        }
        #EffectEdit:focus {
            border: 1px solid #4da3ff;
        }
        """)

    # ---- Autosave wiring ----

    def _wire_autosave(self):
        """///summary: Connecte les changements UI pour autosave (existant uniquement)."""
        def trigger():
            if self._is_loading:
                return
            # Auto-save uniquement si on édite un existant
            if self._current_original_name:
                self._autosave_timer.start()

        # Laisser le rename s'autosauver après debounce (optionnel : utiliser textEdited)
        self.ed_name.textEdited.connect(trigger)
        self.ed_diff.textEdited.connect(trigger)
        self.ed_short.textEdited.connect(trigger)
        self.ed_effect.textChanged.connect(trigger)

        self.cat_toggle.changed.connect(trigger)
        self.books_check.changed.connect(trigger)
        self.origins_tree.changed.connect(trigger)

    # ---- Data wiring ----

    def refresh(self):
        # sources de filtres
        fs = self.presenters["ingredients"].get_filter_sources()
        # catégories
        self.cmb_cat.blockSignals(True)
        self.cmb_cat.clear()
        self.cmb_cat.addItem("(Toutes)")
        for c in fs.categories:
            self.cmb_cat.addItem(c)
        self.cmb_cat.blockSignals(False)
        # livres
        self.cmb_book.blockSignals(True)
        self.cmb_book.clear()
        self.cmb_book.addItem("(Tous)")
        for b in fs.books:
            self.cmb_book.addItem(b)
        self.cmb_book.blockSignals(False)
        # trees
        tree = self.repos["data"].get_origin_tree()
        self.origins_tree.set_tree(tree)
        # bouton filtre origine
        self._origin_filter_btn.set_tree(tree)
        # books checklist refresh
        self.books_check.populate(fs.books)

        self._refresh_list()

    def _toggle_filters(self, visible: bool):
        self.filters.setVisible(visible)

    def _current_filters(self) -> Tuple[str, Optional[str], Optional[str], Optional[str]]:
        q = self.search.text().strip()
        cat = self.cmb_cat.currentText()
        book = self.cmb_book.currentText()
        origin_label = self._origin_filter_btn.selected_label()
        return (q, cat, book if book != "(Tous)" else None, origin_label)

    def _refresh_list(self):
        q = self.search.text().strip()
        cat = self.cmb_cat.currentText()
        book = self.cmb_book.currentText()
        origin_label = self._origin_filter_btn.selected_label()  # label court

        vms = self.presenters["ingredients"].list_ingredients(
            query=q,
            cat=cat,
            book=(None if book in ("", "(Tous)") else book),
            origin=origin_label,
        )

        order = {"Liant": 0, "Catalyseur": 1, "Réactif": 2}
        vms.sort(key=lambda vm: (order.get(vm.category, 99), vm.name.lower()))
        self.list.clear()
        for vm in vms:
            text = f"{self._cat_emoji(vm.category)} {vm.name}".strip()
            it = QListWidgetItem(text)
            it.setData(Qt.UserRole, vm.name)
            it.setToolTip(f"{vm.category} • Diff {vm.difficulty}")
            self.list.addItem(it)

    # ---- Selection / load ----

    def _activate_selected(self):
        names = self._selected_names()
        if not names:
            return
        self._load_into_editor(names[0])

    def _selected_names(self) -> List[str]:
        out = []
        for it in self.list.selectedItems():
            name = it.data(Qt.UserRole)
            if name:
                out.append(name)
        return out

    def _load_into_editor(self, name: str):
        try:
            ing = self.repos["ingredients"].get_by_name(name)
        except Exception as e:
            error(self, f"Impossible de charger l'ingrédient {name!r}.\n{e}")
            return

        self._is_loading = True
        try:
            self._current_original_name = ing.name

            self.ed_name.setText(ing.name)
            self.cat_toggle.set_value(ing.cat)
            self.ed_diff.setText(str(ing.difficulty))
            self.ed_short.setText(ing.short_effect or "")
            self.ed_effect.setPlainText(ing.effect or "")
            self.books_check.set_checked(ing.books or [])
            self.origins_tree.set_checked_paths(ing.origins or [])
        finally:
            self._is_loading = False

    def _new(self):
        self._is_loading = True
        try:
            self._current_original_name = None
            self.ed_name.clear()
            self.cat_toggle.set_value("")
            self.ed_diff.clear()
            self.ed_short.clear()
            self.ed_effect.clear()
            self.books_check.set_checked([])
            self.origins_tree.set_checked_paths([])
        finally:
            self._is_loading = False

    # ---- CRUD ----

    def _collect_form(self) -> Tuple[str, str, int, str, str, List[str], List[str]]:
        name = self.ed_name.text().strip()
        cat = self.cat_toggle.get_value()
        try:
            difficulty = int(self.ed_diff.text().strip() or "0")
        except Exception:
            raise ValidationError("La difficulté doit être un entier (positif, nul ou négatif).")
        shortEffect = self.ed_short.text().strip()
        effect = self.ed_effect.toPlainText().strip()
        books = self.books_check.get_checked()
        origins_paths = self.origins_tree.get_checked_paths()
        # On enregistre uniquement les *labels* (dernier segment)
        origins = [p.split("/")[-1] for p in origins_paths]
        return name, cat, difficulty, shortEffect, effect, books, origins

    def _save(self, *, autosave: bool=False):
        """///summary: Sauvegarde. En mode autosave, pas de popup info et on restaure l'état UI."""
        try:
            name, cat, difficulty, shortEffect, effect, books, origins = self._collect_form()
            if not name:
                if autosave:
                    return  # on ne force pas d'erreur UI pendant saisie
                raise ValidationError("Le nom est obligatoire.")
            if not cat:
                if autosave:
                    return
                raise ValidationError("Veuillez choisir une catégorie.")

            existing_names = {i.name for i in self.repos["ingredients"].list_all()}

            # ///summary: mémoriser état UI pour éviter “disparition” post-refresh
            kept_cat = cat
            kept_books = list(books)
            kept_origins_paths = self.origins_tree.get_checked_paths()

            if self._current_original_name is None:
                # CREATE
                self.uc["create"].execute(
                    name=name, cat=cat, difficulty=difficulty,
                    shortEffect=shortEffect, effect=effect,
                    books=books, origins=origins
                )

                # Mise à jour de la liste
                self._is_loading = True
                try:
                    self.refresh()
                    # ///summary: remise à zéro pour enchaîner une nouvelle saisie
                    self._new()
                    # garder Catégorie + Livres + (option) Origines si utile
                    self.cat_toggle.set_value(kept_cat)
                    self.books_check.set_checked(kept_books)
                    self.origins_tree.set_checked_paths(kept_origins_paths)
                finally:
                    self._is_loading = False

                self._current_original_name = None
                self.ed_name.setFocus()
                if not autosave:
                    info(self, f"Ingrédient {name!r} créé. Saisie d'un nouvel ingrédient prête.")
                return

            # --- cas EXISTANT ---
            original = self._current_original_name
            if name == original:
                # UPDATE
                self.uc["update"].execute(
                    name=name, cat=cat, difficulty=difficulty,
                    shortEffect=shortEffect, effect=effect,
                    books=books, origins=origins
                )
            else:
                # RENAME
                if name in existing_names:
                    if autosave:
                        return
                    raise DuplicateNameError(f"Un ingrédient nommé {name!r} existe déjà.")
                self.uc["create"].execute(
                    name=name, cat=cat, difficulty=difficulty,
                    shortEffect=shortEffect, effect=effect,
                    books=books, origins=origins
                )
                self.uc["delete"].execute(original)
                self._current_original_name = name
                if not autosave:
                    info(self, f"Ingrédient renommé en {name!r} et enregistré.")

            # ///summary: refresh en conservant l’état UI (Livres/Origines visibles)
            self._is_loading = True
            try:
                self.refresh()
                self._select_in_list(self._current_original_name or name)
                # Restaure visuellement (au cas où refresh reconstruit les widgets)
                self.cat_toggle.set_value(kept_cat)
                self.books_check.set_checked(kept_books)
                self.origins_tree.set_checked_paths(kept_origins_paths)
            finally:
                self._is_loading = False

            if not autosave:
                info(self, f"Ingrédient {self._current_original_name!r} enregistré.")

        except PotionDBError as e:
            if not autosave:
                error(self, str(e))
        except Exception as e:
            if not autosave:
                error(self, f"Erreur inattendue : {e}")

    def _select_in_list(self, name: str):
        for i in range(self.list.count()):
            it = self.list.item(i)
            if it.data(Qt.UserRole) == name:
                self.list.setCurrentItem(it)
                break

    def _delete_current(self):
        if not self._current_original_name:
            warn(self, "Aucun ingrédient en édition.")
            return
        self._delete_by_names([self._current_original_name])

    def _delete_selected(self):
        names = self._selected_names()
        if not names:
            return
        self._delete_by_names(names)

    def _delete_by_names(self, names: List[str]):
        if not names:
            return
        reply = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Supprimer {len(names)} ingrédient(s) sélectionné(s) ?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            for n in names:
                self.uc["delete"].execute(n)
            info(self, "Suppression effectuée.")
            if self._current_original_name in names:
                self._new()
            self.refresh()
        except PotionDBError as e:
            error(self, str(e))
        except Exception as e:
            error(self, f"Erreur inattendue : {e}")

    def _duplicate_current(self):
        if not self._current_original_name:
            warn(self, "Aucun ingrédient en édition.")
            return
        try:
            new_name = self.uc["duplicate"].execute(self._current_original_name)
            info(self, f"Dupliqué sous {new_name!r}.")
            self.refresh()
            self._load_into_editor(new_name)
            self._select_in_list(new_name)
        except PotionDBError as e:
            error(self, str(e))
        except Exception as e:
            error(self, f"Erreur inattendue : {e}")
