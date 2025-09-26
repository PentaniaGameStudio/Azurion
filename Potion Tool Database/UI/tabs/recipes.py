from __future__ import annotations
from typing import List, Optional, Tuple, Dict

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
    QListWidget, QListWidgetItem, QLineEdit, QLabel,
    QPushButton, QToolButton, QFrame, QComboBox, QDialog,
    QMessageBox, QSplitter, QGroupBox, QDialogButtonBox, QCheckBox,
    QScrollArea, QSizePolicy, QTextEdit
)

from domain.errors import PotionDBError, ValidationError, DuplicateNameError
from UI.tabs.ingredients import BooksChecklist

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
    Double-clic remonte un callback fourni.
    """
    def __init__(self, on_delete_callback=None, on_activate_callback=None, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QListWidget.ExtendedSelection)
        self._on_delete = on_delete_callback
        self._on_activate = on_activate_callback
        if on_activate_callback:
            self.itemDoubleClicked.connect(lambda _: on_activate_callback())

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            if self._on_delete:
                self._on_delete()
            e.accept()
            return
        super().keyPressEvent(e)


# ---------- Dialog d’édition d’une alternative ----------

class ComboDialog(QDialog):
    """
    ///summary: Édite une alternative d'ingrédients (liant?, catalyseur?, ≥1 réactif).
    Affiche l'effet court entre parenthèses *uniquement* dans ce dialog.
    On renvoie une liste concaténée: [liant?, catalyseur?, reactif...]
    """
    def __init__(
        self,
        recipes_presenter,
        parent=None,
        initial: Optional[List[str]] = None,
        short_effects: Optional[Dict[str, str]] = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Alternative d'ingrédients")
        self.presenter = recipes_presenter
        self.short_effects = short_effects or {}

        # Sources (noms “bruts”)
        liants = self.presenter.get_ingredients_by_category("Liant")
        catas  = self.presenter.get_ingredients_by_category("Catalyseur")
        reac   = self.presenter.get_ingredients_by_category("Réactif")

        def label_for(name: str) -> str:
            se = self.short_effects.get(name, "").strip()
            return f"{name} ({se})" if se else name

        lay = QVBoxLayout(self)

        grid = QGridLayout()
        row = 0

        # Liant
        self.cmb_liant = QComboBox()
        self.cmb_liant.addItem("(Aucun)", "")  # userData = nom brut (vide)
        for n in liants:
            self.cmb_liant.addItem(label_for(n), n)  # display “Nom (effet)”, data “Nom”
        grid.addWidget(QLabel("Liant (optionnel)"), row, 0)
        grid.addWidget(self.cmb_liant, row, 1); row += 1

        # Catalyseur
        self.cmb_cata = QComboBox()
        self.cmb_cata.addItem("(Aucun)", "")
        for n in catas:
            self.cmb_cata.addItem(label_for(n), n)
        grid.addWidget(QLabel("Catalyseur (optionnel)"), row, 0)
        grid.addWidget(self.cmb_cata, row, 1); row += 1

        # Réactifs multi: grille scrollable horizontale (10 lignes max)
        reac_names = sorted(reac)

        box = QGroupBox("Réactifs (au moins 1)")
        box_lay = QVBoxLayout(box)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        container = QWidget()
        rGrid = QGridLayout(container)
        rGrid.setContentsMargins(0, 0, 0, 0)
        rGrid.setSpacing(6)

        self.reac_checks: List[QCheckBox] = []
        for i, name in enumerate(reac_names):
            r = i % 10          # 10 lignes max
            c = i // 10         # nouvelles colonnes à droite
            cb = QCheckBox(label_for(name))
            cb.setProperty("raw_name", name)  # ///summary: conserve le nom brut
            self.reac_checks.append(cb)
            rGrid.addWidget(cb, r, c)

        container.setLayout(rGrid)
        scroll.setWidget(container)

        # Hauteur confortable pour 10 lignes (ajuste si besoin)
        scroll.setMinimumHeight(10 * 35 + 75)

        box_lay.addWidget(scroll)

        lay.addLayout(grid)
        lay.addWidget(box)

        # Boutons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

        # Pré-remplissage si édition (basé sur les noms bruts)
        if initial:
            init_set = set(initial)
            # liant
            idx = self.cmb_liant.findData(next((n for n in liants if n in init_set), ""), Qt.UserRole)
            if idx >= 0:
                self.cmb_liant.setCurrentIndex(idx)
            # cata
            idx = self.cmb_cata.findData(next((n for n in catas if n in init_set), ""), Qt.UserRole)
            if idx >= 0:
                self.cmb_cata.setCurrentIndex(idx)
            # réactifs
            for cb in self.reac_checks:
                raw = cb.property("raw_name") or ""
                cb.setChecked(raw in init_set)

        # style
        self.setMinimumWidth(420)

    def _accept(self):
        liant = self.cmb_liant.currentData() or ""
        cata  = self.cmb_cata.currentData() or ""

        reactifs = []
        for cb in self.reac_checks:
            if cb.isChecked():
                raw = cb.property("raw_name") or ""
                if raw:
                    reactifs.append(raw)

        if not reactifs:
            error(self, "Veuillez sélectionner au moins un réactif.")
            return

        combo: List[str] = []
        if liant: combo.append(liant)
        if cata:  combo.append(cata)
        combo.extend(reactifs)

        self._result = combo
        self.accept()

    def result_combo(self) -> List[str]:
        return getattr(self, "_result", [])


# ---------- Onglet Recettes ----------

class RecipesTab(QWidget):
    def __init__(self, container, parent=None):
        super().__init__(parent)
        self.container = container
        self.presenters = container["presenters"]
        self.repos = container["repos"]
        self.uc = container["use_cases"]["recipes"]   # {create, update, delete, duplicate}

        self._current_original_name: Optional[str] = None

        # ///summary: autosave (300ms debounce) + garde-fou pendant chargements
        self._is_loading = False
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.setInterval(300)
        self._autosave_timer.timeout.connect(lambda: self._save(autosave=True))

        self._build_ui()
        self._wire_autosave()
        self.refresh()

    # ---- UI ----

    def _build_ui(self):
        root = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter)

        # --- LEFT: liste + recherche ---
        left = QWidget()
        left_lay = QVBoxLayout(left)

        topbar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Rechercher...")
        topbar.addWidget(self.search, 1)
        left_lay.addLayout(topbar)

        self.list = DeletableList(self._delete_selected, self._activate_selected)
        left_lay.addWidget(self.list, 1)

        splitter.addWidget(left)

        # --- RIGHT: éditeur ---
        right = QWidget()
        form = QGridLayout()
        row = 0

        self.ed_name = QLineEdit()
        form.addWidget(QLabel("Nom de la recette"), row, 0)
        form.addWidget(self.ed_name, row, 1); row += 1

        # Emoji + presets
        emoji_bar = QHBoxLayout()
        self.ed_emoji = QLineEdit()
        self.ed_emoji.setText("🧪")
        self.ed_emoji.setMaxLength(3)  # 1 emoji (UTF-16 surrogate pairs ; limite courte)
        emoji_bar.addWidget(self.ed_emoji, 1)
        for sym in ("🧪", "🧫", "🧼", "💊"):
            b = QToolButton(text=sym)
            b.clicked.connect(lambda _=False, s=sym: self.ed_emoji.setText(s))
            emoji_bar.addWidget(b)
        form.addWidget(QLabel("Emoji"), row, 0)
        form.addLayout(emoji_bar, row, 1); row += 1

        # Bonus >= 0
        self.ed_bonus = QLineEdit()
        self.ed_bonus.setPlaceholderText("0 (optionnel, ≥ 0)")
        self.ed_bonus.setValidator(QIntValidator(0, 999999, self))
        form.addWidget(QLabel("Bonus"), row, 0)
        form.addWidget(self.ed_bonus, row, 1); row += 1

        # Description (nouveau)
        self.ed_desc = QTextEdit()
        self.ed_desc.setObjectName("DescEdit")
        self.ed_desc.setPlaceholderText("Description de la potion…")
        fm = self.ed_desc.fontMetrics()
        self.ed_desc.setFixedHeight((fm.lineSpacing() + 6) * 4)  # ~3-4 lignes
        form.addWidget(QLabel("Description"), row, 0)
        form.addWidget(self.ed_desc, row, 1); row += 1

        # Livres
        self.books_widget = BooksChecklist(self.repos["data"].get_books(), self)
        form.addWidget(QLabel("Livres"), row, 0)
        form.addWidget(self.books_widget, row, 1); row += 1
        
        # Alternatives (combos)
        combos_box = QGroupBox("Alternatives d'ingrédients")
        combos_lay = QVBoxLayout(combos_box)
        self.combos = DeletableList(self._delete_combo, self._edit_combo)
        combos_btns = QHBoxLayout()
        btn_add_combo = QPushButton("Ajouter")
        btn_add_combo.clicked.connect(self._add_combo)
        combos_btns.addStretch(1)
        combos_btns.addWidget(btn_add_combo)
        combos_lay.addWidget(self.combos, 1)
        combos_lay.addLayout(combos_btns)

        form.addWidget(combos_box, row, 0, 1, 2); row += 1

        # Boutons CRUD (centrés)
        btns = QHBoxLayout()
        self.btn_new = QPushButton("Nouveau")
        self.btn_dup = QPushButton("Dupliquer")
        self.btn_save = QPushButton("Enregistrer")
        self.btn_del = QPushButton("Supprimer")

        self.btn_new.clicked.connect(self._new)
        self.btn_dup.clicked.connect(self._duplicate_current)
        self.btn_save.clicked.connect(lambda: self._save(autosave=False))
        self.btn_del.clicked.connect(self._delete_current)

        btns.addStretch(1)  # ///summary: centre les boutons
        for b in (self.btn_new, self.btn_dup, self.btn_save, self.btn_del):
            btns.addWidget(b)
        btns.addStretch(1)

        wrap = QVBoxLayout()
        wrap.addLayout(form, 1)
        wrap.addLayout(btns, 0)
        right.setLayout(wrap)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        # interactions
        self.search.textChanged.connect(self._refresh_list)

        # style léger
        self.setStyleSheet("""
        QListWidget { min-height: 140px; }
        #DescEdit {
            border: 1px solid transparent;
            border-radius: 6px;
            padding: 6px;
        }
        #DescEdit:hover { border: 1px solid rgba(77,163,255,0.35); }
        #DescEdit:focus { border: 1px solid #4da3ff; }
        """)

    # ---- Autosave wiring ----

    def _wire_autosave(self):
        """///summary: Connecte les changements UI -> autosave (si édition d'un existant)."""
        def trigger():
            if self._is_loading:
                return
            if self._current_original_name:
                self._autosave_timer.start()

        # Champs texte
        self.ed_name.textEdited.connect(trigger)
        self.ed_emoji.textEdited.connect(trigger)
        self.ed_bonus.textEdited.connect(trigger)
        self.ed_desc.textChanged.connect(trigger)

        # Livres (BooksChecklist émet .changed dans IngredientsTab)
        self.books_widget.changed.connect(trigger)

        # Combos : on déclenchera manuellement après add/edit/delete
        self._autosave_trigger = trigger  # stocke pour réutiliser facilement

    def _trigger_autosave_now(self):
        """///summary: Helper pour déclencher l'autosave depuis les actions combos."""
        if not self._is_loading and self._current_original_name:
            self._autosave_timer.start()

    # ---- Data wiring ----

    def refresh(self):
        # liste des recettes + livres
        self._refresh_books_checklist()
        self._refresh_list()

    def _refresh_books_checklist(self):
        """///summary: Recharge la liste des livres depuis le repo, en préservant la sélection."""
        try:
            current_checked = self.books_widget.get_checked()
        except Exception:
            current_checked = []
        books = self.repos["data"].get_books()
        self.books_widget.populate(books)
        self.books_widget.set_checked([b for b in current_checked if b in books])

    def _refresh_list(self):
        q = self.search.text().strip()
        vms = self.presenters["recipes"].list_recipes(query=q)
        self.list.clear()
        for vm in vms:
            it = QListWidgetItem(vm.title)
            it.setData(Qt.UserRole, vm.name)
            self.list.addItem(it)

    # ---- Selection / load ----

    def _activate_selected(self):
        names = self._selected_names()
        if not names:
            return
        self._load_into_editor(names[0])

    def _selected_names(self) -> List[str]:
        return [it.data(Qt.UserRole) for it in self.list.selectedItems() if it.data(Qt.UserRole)]

    def _load_into_editor(self, name: str):
        try:
            rec = self.repos["recipes"].get_by_name(name)
        except Exception as e:
            error(self, f"Impossible de charger la recette {name!r}.\n{e}")
            return

        self._is_loading = True
        try:
            self._current_original_name = rec.name
            self.ed_name.setText(rec.name or "")
            self.ed_emoji.setText(rec.emoji or "🧪")
            self.ed_bonus.setText("" if rec.bonus in (None, "") else str(int(rec.bonus)))
            self.ed_desc.setPlainText(getattr(rec, "desc", "") or "")
            self.books_widget.set_checked(list(getattr(rec, "books", []) or []))
            self._set_combos(rec.combos or [])
        finally:
            self._is_loading = False

    def _new(self):
        """///summary: Réinitialise pour saisir une nouvelle recette (mode 'Nouveau')."""
        self._is_loading = True
        try:
            self._current_original_name = None
            self.ed_name.clear()
            self.ed_emoji.setText("🧪")
            self.ed_bonus.setText("0")
            self.ed_desc.clear()
            self.books_widget.set_checked([])
            self._set_combos([])
        finally:
            self._is_loading = False

    # ---- Combos helpers ----

    def _set_combos(self, combos: List[List[str]]):
        self.combos.clear()
        for c in combos or []:
            self._append_combo_item(list(c))

    def _append_combo_item(self, combo: List[str], at_index: Optional[int] = None):
        text = " • ".join(combo)  # ///summary: on affiche les noms bruts
        it = QListWidgetItem(text)
        it.setData(Qt.UserRole, combo)
        if at_index is None:
            self.combos.addItem(it)
        else:
            self.combos.insertItem(at_index, it)

    def _current_combos(self) -> List[List[str]]:
        out: List[List[str]] = []
        for i in range(self.combos.count()):
            it = self.combos.item(i)
            combo = it.data(Qt.UserRole) or []
            out.append(list(combo))
        return out

    def _selected_combo_rows(self) -> List[int]:
        rows = sorted([self.combos.row(it) for it in self.combos.selectedItems()])
        return rows

    # ---- Combos actions ----

    def _short_effect_map(self) -> Dict[str, str]:
        """///summary: Map {ing_name: short_effect} pour enrichir l'affichage du dialog."""
        m: Dict[str, str] = {}
        try:
            for ing in self.repos["ingredients"].list_all():
                se = getattr(ing, "short_effect", None) or getattr(ing, "shortEffect", None)
                if se:
                    m[ing.name] = str(se)
        except Exception:
            pass
        return m

    def _add_combo(self):
        dlg = ComboDialog(self.presenters["recipes"], self, short_effects=self._short_effect_map())
        if dlg.exec() == QDialog.Accepted:
            combo = dlg.result_combo()
            self._append_combo_item(combo)
            self._trigger_autosave_now()  # ///summary: autosave après ajout

    def _edit_combo(self):
        rows = self._selected_combo_rows()
        if not rows:
            return
        row = rows[0]
        it = self.combos.item(row)
        initial = list(it.data(Qt.UserRole) or [])
        dlg = ComboDialog(
            self.presenters["recipes"], self,
            initial=initial, short_effects=self._short_effect_map()
        )
        if dlg.exec() == QDialog.Accepted:
            combo = dlg.result_combo()
            it.setText(" • ".join(combo))
            it.setData(Qt.UserRole, combo)
            self._trigger_autosave_now()  # ///summary: autosave après édition

    def _delete_combo(self):
        rows = list(reversed(self._selected_combo_rows()))
        if not rows:
            return
        for r in rows:
            self.combos.takeItem(r)
        self._trigger_autosave_now()  # ///summary: autosave après suppression

    # ---- CRUD ----

    def _collect_form(self) -> Tuple[str, str, Optional[float], List[List[str]], List[str], str]:
        """///summary: Lit le formulaire et valide (hors autosave)."""
        name = self.ed_name.text().strip()
        emoji = self.ed_emoji.text().strip() or "🧪"
        # bonus: vide -> 0 ; sinon int >= 0
        btxt = self.ed_bonus.text().strip()
        bonus: Optional[float] = None
        if btxt == "":
            bonus = 0.0
        else:
            try:
                val = int(btxt)
                if val < 0:
                    raise ValidationError("Le bonus ne peut pas être négatif.")
                bonus = float(val)
            except Exception:
                raise ValidationError("Le bonus doit être un entier positif.")
        combos = self._current_combos()
        if not combos:
            raise ValidationError("Ajoutez au moins une alternative d'ingrédients.")
        books = self.books_widget.get_checked()
        desc = self.ed_desc.toPlainText().strip()
        return name, emoji, bonus, combos, books, desc

    def _collect_form_lenient(self) -> Optional[Tuple[str, str, Optional[float], List[List[str]], List[str], str]]:
        """///summary: Version indulgente pour l'auto-save (ignore si incomplet)."""
        name = self.ed_name.text().strip()
        if not name:
            return None
        emoji = self.ed_emoji.text().strip() or "🧪"
        btxt = self.ed_bonus.text().strip()
        if btxt == "":
            bonus = 0.0
        else:
            try:
                val = int(btxt)
                if val < 0:
                    return None
                bonus = float(val)
            except Exception:
                return None
        combos = self._current_combos()
        if not combos:
            return None
        books = self.books_widget.get_checked()
        desc = self.ed_desc.toPlainText().strip()
        return name, emoji, bonus, combos, books, desc

    # -- Use cases wrappers tolérants (desc optionnelle côté backend) --

    def _uc_create(self, **kwargs):
        """///summary: Appelle create(...) et retombe sans 'desc' si non supporté."""
        try:
            self.uc["create"].execute(**kwargs)
        except TypeError:
            kwargs.pop("desc", None)
            self.uc["create"].execute(**kwargs)

    def _uc_update(self, **kwargs):
        """///summary: Appelle update(...) et retombe sans 'desc' si non supporté."""
        try:
            self.uc["update"].execute(**kwargs)
        except TypeError:
            kwargs.pop("desc", None)
            self.uc["update"].execute(**kwargs)

    def _save(self, *, autosave: bool=False):
        """
        ///summary: Sauvegarde.
        - autosave=True: silencieux, ignore si formulaire incomplet.
        - autosave=False: valide strictement et affiche les messages.
        """
        try:
            if autosave:
                pack = self._collect_form_lenient()
                if pack is None:
                    return  # formulaire pas assez complet pour une sauvegarde utile
                name, emoji, bonus, combos, books, desc = pack
            else:
                name, emoji, bonus, combos, books, desc = self._collect_form()
                if not name:
                    raise ValidationError("Le nom de la recette est obligatoire.")

            existing_names = {r.name for r in self.repos["recipes"].list_all()}

            if self._current_original_name is None:
                # --- CREATE ---
                self._uc_create(
                    name=name, emoji=emoji, bonus=bonus, combos=combos,
                    books=books, desc=desc
                )

                # ///summary: passer en mode 'Nouveau' pour enchaîner une autre création
                self._is_loading = True
                try:
                    self.refresh()      # le nouvel item apparaît en liste
                    self._new()         # réinitialise le formulaire
                    self.ed_name.setFocus()
                finally:
                    self._is_loading = False

                if not autosave:
                    info(self, f"Recette {name!r} créée. Prêt pour une nouvelle saisie.")
                return

            # --- EXISTANT ---
            original = self._current_original_name
            if name == original:
                # UPDATE
                self._uc_update(
                    name=name, emoji=emoji, bonus=bonus, combos=combos,
                    books=books, desc=desc
                )
                if not autosave:
                    info(self, f"Recette {name!r} enregistrée.")
            else:
                # RENAME (create + delete old)
                if name in existing_names:
                    if autosave:
                        return
                    raise DuplicateNameError(f"Une recette nommée {name!r} existe déjà.")
                self._uc_create(
                    name=name, emoji=emoji, bonus=bonus, combos=combos,
                    books=books, desc=desc
                )
                self.uc["delete"].execute(original)
                self._current_original_name = name
                if not autosave:
                    info(self, f"Recette renommée en {name!r} et enregistrée.")

            # ///summary: refresh liste et resélectionne l'élément courant
            self._is_loading = True
            try:
                self.refresh()
                self._select_in_list(self._current_original_name or name)
            finally:
                self._is_loading = False

        except ValidationError as e:
            if not autosave:
                error(self, str(e))
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
            warn(self, "Aucune recette en édition.")
            return
        self._delete_by_names([self._current_original_name])

    def _delete_selected(self):
        names = self._selected_names()
        if not names:
            return
        self._delete_by_names(names)

    def _delete_by_names(self, names: List[str]):
        reply = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Supprimer {len(names)} recette(s) sélectionnée(s) ?",
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
            warn(self, "Aucune recette en édition.")
            return
        try:
            new_name = self.uc["duplicate"].execute(self._current_original_name)
            info(self, f"Dupliquée sous {new_name!r}.")
            self.refresh()
            self._load_into_editor(new_name)
            self._select_in_list(new_name)
        except PotionDBError as e:
            error(self, str(e))
        except Exception as e:
            error(self, f"Erreur inattendue : {e}")
