# -*- coding: utf-8 -*-
"""
///summary
Formulaire GUI: création de compétence
- Première ligne plus grosse: Famille (30%) + Nom (70%)
- Dropdown familles = "émojis — nom" mais stockage = émojis
- Tous les champs dans une zone scrollable (molette OK)
- Boutons fixes en bas (toujours visibles) : Enregistrer / Vider / Rafraîchir familles
- Sélecteur de type pour "Difficultés / Facilités" : boutons "Difficulté" / "Facilité" + champ valeur
"""
import tkinter as tk
from tkinter import ttk, messagebox
import platform
import tkinter.font as tkfont

from .datastore import DataStore
from .models import Skill
from .widgets import LabeledEntry, LabeledText, ScrollableFrame

PAD = 8

class CreateSkillFrame(ttk.Frame):
    def __init__(self, master, store: DataStore):
        super().__init__(master, padding=PAD)
        self.store = store
        self._display_to_emojis = {}  # "🌊 — Magie d'Eau" -> "🌊"

        # Titre
        ttk.Label(self, text="Créer une Compétence", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, PAD))

        # Zone scrollable pour tous les champs
        scroll = ScrollableFrame(self)
        scroll.pack(fill="both", expand=True, pady=(0, PAD))
        self._scroll = scroll                 # ← garde une ref. pour suspend_wheel/resume_wheel
        body = scroll.body
        
        # --- Ligne "Niveau" (AVANT Famille/Nom) ---
        level_row = ttk.Frame(body)
        level_row.pack(fill="x", pady=(0, PAD))  # première ligne du formulaire
        ttk.Label(level_row, text="Niveau :", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 6))
        self.level_var = tk.StringVar(value="Niv1")
        for label in ("Niv1", "Niv2", "Niv3"):
            ttk.Radiobutton(level_row, text=label, value=label, variable=self.level_var).pack(side="left", padx=(4, 0))


        # === Première ligne (plus grosse) : Famille (30%) + Nom (70%)
        header = ttk.Frame(body)
        header.pack(fill="x", pady=(0, PAD))
        header.grid_columnconfigure(0, weight=2)  # 30%
        header.grid_columnconfigure(1, weight=7)  # 70%

        # Famille
        fam_col = ttk.Frame(header)
        fam_col.grid(row=0, column=0, sticky="ew", padx=(0, PAD))
        self.lbl_family = ttk.Label(fam_col, text="Famille *")  # ← référence
        self.lbl_family.pack(anchor="w")
        self.family_var = tk.StringVar(value="")
        self.family_cb = ttk.Combobox(fam_col, textvariable=self.family_var, values=(), state="readonly")
        self.family_cb.pack(fill="x")
        
        # Nom
        name_col = ttk.Frame(header)
        name_col.grid(row=0, column=1, sticky="ew")
        self.lbl_name = ttk.Label(name_col, text="Nom *")  # ← référence
        self.lbl_name.pack(anchor="w")
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(name_col, textvariable=self.name_var)
        self.name_entry.pack(fill="x")
        
        self._apply_big_header_fonts()
        self._install_combobox_scroll_guard(self.family_cb)
        
        # Astuce si aucune famille
        if not self.store.families:
            ttk.Label(
                body,
                foreground="#a33",
                wraplength=520,
                text="Astuce: vous n'avez pas encore de famille. Créez-en une via le bouton 'Créer Famille'."
            ).pack(anchor="w", pady=(PAD, 0))

        # --- Ligne "Difficulté / Facilité" ---
        diff_row = ttk.Frame(body)
        diff_row.pack(fill="x", pady=(0, PAD))

        ttk.Label(diff_row, text="Type :", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 6))
        self.diff_type_var = tk.StringVar(value="Difficulté")
        ttk.Radiobutton(diff_row, text="Difficulté", value="Difficulté", variable=self.diff_type_var).pack(side="left")
        ttk.Radiobutton(diff_row, text="Facilité", value="Facilité", variable=self.diff_type_var).pack(side="left", padx=(8, 0))
        ttk.Radiobutton(diff_row, text="Passif", value="Passif", variable=self.diff_type_var).pack(side="left", padx=(8, 0))

        self.diff_value = LabeledEntry(body, "Valeur (ex: -2 aux jets d'attaque)")
        self.diff_value.pack(fill="x", pady=(0, PAD))

        # Champs simples
        self.cost = LabeledEntry(body, "Coût")
        self.target = LabeledEntry(body, "Cible")
        self.range_ = LabeledEntry(body, "Portée")
        self.duration = LabeledEntry(body, "Durée")
        self.damage = LabeledEntry(body, "Dégâts")

        for w in (self.cost, self.target, self.range_, self.duration, self.damage):
            w.pack(fill="x", pady=(0, PAD))

        # Champs multi-lignes
        self.effects = LabeledText(body, "Effet(s)")
        self.conditions = LabeledText(body, "Condition(s)")
        self.limits = LabeledText(body, "Limite(s)")
        self.effects.pack(fill="both", expand=True, pady=(0, PAD))
        self.conditions.pack(fill="both", expand=True, pady=(0, PAD))
        self.limits.pack(fill="both", expand=True, pady=(0, PAD))

        # ///summary: Case à cocher "Masquer cet item dans les index"
        hide_row = ttk.Frame(body)
        hide_row.pack(fill="x", pady=(0, PAD))
        self.hidden_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(hide_row, text="Masquer dans les index (hided)", variable=self.hidden_var).pack(anchor="w")


        # Boutons fixes (hors zone scrollable)
        btns = ttk.Frame(self)
        btns.pack(fill="x", pady=(PAD, 0))
        ttk.Button(btns, text="Enregistrer", command=self._save).pack(side="left")
        ttk.Button(btns, text="Vider le formulaire", command=self._clear).pack(side="left", padx=(PAD, 0))
        ttk.Button(btns, text="Rafraîchir familles", command=self._refresh_families).pack(side="left", padx=(PAD, 0))

        # Init des familles pour le dropdown
        self._refresh_families()

    def _emoji_font_name(self) -> str:
        # Police emoji selon l’OS (fallback si introuvable)
        sysname = platform.system()
        if sysname == "Windows":
            return "Segoe UI Emoji"
        if sysname == "Darwin":
            return "Apple Color Emoji"
        return "Noto Color Emoji"  # Linux

    def _apply_big_header_fonts(self, emoji_pt: int = 18, name_pt: int = 13, label_pt: int = 12):
        # Police pour les émojis dans le Combobox
        try:
            emoji_font = tkfont.Font(family=self._emoji_font_name(), size=emoji_pt)
        except tk.TclError:
            emoji_font = tkfont.Font(size=emoji_pt)  # fallback

        # Police labels en gras
        label_bold = tkfont.Font(size=label_pt, weight="bold")
        # Police pour l'Entry Nom
        name_font = tkfont.Font(size=name_pt)

        # 1) Entrée du Combobox (zone éditable) → emoji plus gros
        self.family_cb.configure(font=emoji_font)

        # 2) Liste déroulante du Combobox → la même police (emoji gros dans le menu)
        #    Global pour tous les Combobox (simple et fiable)
        self.option_add("*TCombobox*Listbox.font", emoji_font)

        # 3) Labels plus lisibles
        self.lbl_family.configure(font=label_bold)
        self.lbl_name.configure(font=label_bold)

        # 4) Champ Nom un peu plus grand
        self.name_entry.configure(font=name_font)


    # ///summary: Construit la liste d’affichage "émojis — nom" et la map display->emojis.
    def _build_family_choices(self):
        pairs = []
        for fam in self.store.families:
            display = f"{fam.emojis} — {fam.name}" if fam.name.strip() else fam.emojis
            pairs.append((display, fam.emojis))
        pairs.sort(key=lambda p: p[0])
        return pairs

    def _refresh_families(self):
        pairs = self._build_family_choices()
        values = [d for d, _ in pairs]
        self._display_to_emojis = {d: e for d, e in pairs}
        self.family_cb["values"] = values
        if values:
            if self.family_var.get() not in values:
                self.family_var.set(values[0])
        else:
            self.family_var.set("")

    def _clear(self) -> None:
        self.name_var.set("")
        self.diff_type_var.set("Difficulté")
        self.diff_value.var.set("")
        self.cost.var.set("")
        self.target.var.set("")
        self.range_.var.set("")
        self.damage.var.set("")
        self.effects.text.delete("1.0", "end")
        self.conditions.text.delete("1.0", "end")
        self.limits.text.delete("1.0", "end")
        self.duration.var.set("")
        self.hidden_var.set(False)



    def _save(self) -> None:
        # Famille (clé émojis) depuis la sélection affichée
        display = self.family_var.get().strip()
        family_emojis = self._display_to_emojis.get(display, "").strip()
        if not family_emojis:
            messagebox.showwarning("Famille requise", "Merci de choisir une famille.")
            return

        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Nom requis", "La compétence doit avoir un nom.")
            return

        # Construit le champ "Difficultés / Facilités" en string
        diff_label = self.diff_type_var.get()
        diff_text = self.diff_value.var.get().strip()
        difficulty_field = f"{diff_label} : {diff_text}" if diff_text else diff_label

        skill = Skill(
            family=family_emojis,  # on stocke uniquement la clé émojis
            name=name,
            cost=self.cost.var.get().strip(),
            difficulty=difficulty_field,          # ← string combiné
            target=self.target.var.get().strip(),
            range_=self.range_.var.get().strip(),
            damage=self.damage.var.get().strip(),
            effects=self.effects.get_lines(),
            conditions=self.conditions.get_lines(),
            limits=self.limits.get_lines(),
            duration=self.duration.var.get().strip(),
            level=self.level_var.get(),
            hided=self.hidden_var.get(),


        )
        try:
            self.store.add_skill(skill)
            messagebox.showinfo("OK", f"Compétence '{name}' ajoutée.")
            self._clear()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    # ///summary
    # Désactive le scroll global quand le dropdown du Combobox est *ouvert*,
    # puis le réactive quand il se *ferme*. S’appuie sur le popdown interne Tk.
    def _install_combobox_scroll_guard(self, combobox: ttk.Combobox):
        # Crée/récupère la fenêtre popdown interne du Combobox
        pop_path = combobox.tk.call("ttk::combobox::PopdownWindow", combobox)
        try:
            pop = self.nametowidget(pop_path)  # Toplevel du dropdown
        except Exception:
            return  # sécurité

        # Ouverture du dropdown → suspend le scroll de la ScrollableFrame
        pop.bind("<Map>", lambda e: self._on_combo_open(), add="+")
        # Fermeture du dropdown → réactive le scroll
        pop.bind("<Unmap>", lambda e: self._on_combo_close(), add="+")

    def _on_combo_open(self):
        if hasattr(self, "_scroll") and self._scroll is not None:
            self._scroll.suspend_wheel()

    def _on_combo_close(self):
        if hasattr(self, "_scroll") and self._scroll is not None:
            self._scroll.resume_wheel()
