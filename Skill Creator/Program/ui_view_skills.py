# -*- coding: utf-8 -*-
"""
///summary
Vue liste + détail des compétences (Liste & Item)
- Colonnes: Famille | Nom | Niv
- Tri: Famille, puis Niv (Niv1<Niv2<Niv3), puis Nom (alphabétique)
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional
from .datastore import DataStore
from .models import Skill

PAD = 8

class ViewSkillsFrame(ttk.Frame):
    COLUMNS = ("family", "name", "level")

    def __init__(self, master, store: DataStore):
        super().__init__(master, padding=PAD)
        self.store = store

        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, PAD))

        ttk.Label(top, text="Rechercher:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(top, textvariable=self.search_var, width=32)
        self.search_entry.pack(side="left", padx=(PAD // 2, PAD))
        self.search_entry.bind("<Return>", lambda e: self.refresh())

        ttk.Button(top, text="Actualiser", command=self.refresh).pack(side="left", padx=(0, PAD))

        # Main split: list (left) + item (right)
        main = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        main.pack(fill="both", expand=True)

        # Left list
        left = ttk.Frame(main)
        self.tree = ttk.Treeview(left, columns=self.COLUMNS, show="headings", selectmode="browse")

        headers = ["Famille", "Nom", "Niv"]
        for col, text in zip(self.COLUMNS, headers):
            self.tree.heading(col, text=text)

        # tailles / alignements
        self.tree.column("family", width=120, anchor="center")
        self.tree.column("name", width=220, anchor="w")
        self.tree.column("level", width=70, anchor="center")

        vsb = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="left", fill="y")
        left.pack(fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # Right detail ("Item")
        right = ttk.Frame(main, padding=PAD)
        self.detail_title = ttk.Label(right, text="Aucune compétence sélectionnée", font=("Segoe UI", 12, "bold"))
        self.detail_title.pack(anchor="w", pady=(0, PAD))

        self.detail_text = tk.Text(right, height=18, wrap="word")
        self.detail_text.configure(state="disabled")
        self.detail_text.pack(fill="both", expand=True)

        # Buttons under detail
        btns = ttk.Frame(right)
        btns.pack(fill="x", pady=(PAD, 0))
        ttk.Button(btns, text="Supprimer", command=self._delete_selected).pack(side="left")
        ttk.Button(btns, text="Exporter la sélection (JSON)", command=self._export_selected).pack(side="left", padx=(PAD, 0))

        main.add(left, weight=3)
        main.add(right, weight=2)

        self.refresh()

    def refresh(self) -> None:
        """Re-populate the tree trié par Famille → Niv → Nom, filtré par recherche."""
        query = self.search_var.get().strip().lower()

        # Clear
        for iid in self.tree.get_children():
            self.tree.delete(iid)

        # mapping d'ordre pour le niveau
        lvl_order_map = {"niv1": 1, "niv2": 2, "niv3": 3}

        rows = []
        for idx, s in enumerate(self.store.skills):
            family = s.family
            name = s.name
            level = getattr(s, "level", "") or ""
            order_level = lvl_order_map.get(level.lower(), 999)

            # Texte de recherche (on garde large)
            searchable_parts = [
                family, name, level,
                getattr(s, "cost", "") or "",
                getattr(s, "difficulty", "") or "",
                getattr(s, "target", "") or "",
                getattr(s, "range_", "") or "",
                getattr(s, "duration", "") or "",
                getattr(s, "damage", "") or "",
                " ".join(getattr(s, "effects", []) or []),
                " ".join(getattr(s, "conditions", []) or []),
                " ".join(getattr(s, "limits", []) or []),
            ]
            searchable = " ".join(searchable_parts).lower()
            if query and query not in searchable:
                continue

            rows.append(((family, order_level, name.lower()), idx, (family, name, level)))

        # Tri demandé: Famille → Niv → Nom
        rows.sort(key=lambda t: t[0])

        # Insert rows
        for _key, idx, values in rows:
            self.tree.insert("", "end", iid=str(idx), values=values)

        # Reset detail
        self._set_detail(None)

    def _on_select(self, _evt=None) -> None:
        sel = self.tree.selection()
        if not sel:
            self._set_detail(None)
            return
        idx = int(sel[0])
        skill = self.store.skills[idx]
        self._set_detail(skill)

    def _set_detail(self, skill: Optional[Skill]) -> None:
        # ///summary
        # Affiche:
        #  Famille Nom (Niv)
        #    Coût : ...
        #    <Difficulté/Facilité> (affiche la chaîne telle quelle)
        #    Cible : ...
        #    Portée : ...
        #    Durée : ...
        #    Dégâts : ...
        #    Effet : x        (si 1)
        #    Effets :         (si >1)
        #      x
        #      y
        #    Condition : x    (si 1)
        #    Conditions :     (si >1)
        #      x
        #      y
        #    Limite : x       (si 1)
        #    Limites :        (si >1)
        #      x
        #      y
        self.detail_text.configure(state="normal")
        self.detail_text.delete("1.0", "end")

        if skill is None:
            self.detail_title.configure(text="Aucune compétence sélectionnée")
            self.detail_text.insert("1.0", "Sélectionnez une compétence dans la liste pour voir ses détails.")
            self.detail_text.configure(state="disabled")
            return

        # Titre (on garde le label au-dessus, et on remet l'entête dans le texte)
        self.detail_title.configure(text=f"{skill.family}  {skill.name}")

        # Récupération/normalisation
        family = getattr(skill, "family", "") or ""
        name = getattr(skill, "name", "") or ""
        level = getattr(skill, "level", "") or ""
        cost = getattr(skill, "cost", "") or ""
        diff = getattr(skill, "difficulty", "") or ""
        target = getattr(skill, "target", "") or ""
        range_ = getattr(skill, "range_", "") or ""
        duration = getattr(skill, "duration", "") or ""
        damage = getattr(skill, "damage", "") or ""

        def _norm_list(lst):
            return [x.strip() for x in (lst or []) if isinstance(x, str) and x.strip()]

        effects = _norm_list(getattr(skill, "effects", []))
        conditions = _norm_list(getattr(skill, "conditions", []))
        limits = _norm_list(getattr(skill, "limits", []))

        lines = []

        # En-tête: Famille Nom (Niv)
        header = f"{family} {name}"
        if level:
            header += f" ({level})"
        lines.append(header)

        # Champs simples (afficher seulement si non vide)
        if cost:
            lines.append(f"\tCoût : {cost}")
        if diff:
            # Le champ contient déjà "Difficulté : ..." ou "Facilité : ..."
            lines.append(f"\t{diff}")
        if target:
            lines.append(f"\tCible : {target}")
        if range_:
            lines.append(f"\tPortée : {range_}")
        if duration:
            lines.append(f"\tDurée : {duration}")
        if damage:
            lines.append(f"\tDégâts : {damage}")

        # Effets
        if len(effects) == 1:
            lines.append(f"\tEffet : {effects[0]}")
        elif len(effects) > 1:
            lines.append("\tEffets :")
            for e in effects:
                lines.append(f"\t\t{e}")

        # Conditions
        if len(conditions) == 1:
            lines.append(f"\tCondition : {conditions[0]}")
        elif len(conditions) > 1:
            lines.append("\tConditions :")
            for c in conditions:
                lines.append(f"\t\t{c}")

        # Limites
        if len(limits) == 1:
            lines.append(f"\tLimite : {limits[0]}")
        elif len(limits) > 1:
            lines.append("\tLimites :")
            for l in limits:
                lines.append(f"\t\t{l}")

        # Rendu
        self.detail_text.insert("1.0", "\n".join(lines))
        self.detail_text.configure(state="disabled")


    def _selected_index(self) -> Optional[int]:
        sel = self.tree.selection()
        if not sel:
            return None
        return int(sel[0])

    def _delete_selected(self) -> None:
        idx = self._selected_index()
        if idx is None:
            messagebox.showinfo("Info", "Aucune compétence sélectionnée.")
            return
        skill = self.store.skills[idx]
        if not messagebox.askyesno("Confirmation", f"Supprimer '{skill.name}' ?"):
            return
        del self.store.skills[idx]
        self.store.save()
        self.refresh()

    def _export_selected(self) -> None:
        idx = self._selected_index()
        if idx is None:
            messagebox.showinfo("Info", "Aucune compétence sélectionnée.")
            return
        s = self.store.skills[idx]
        payload = s.__dict__
        path = filedialog.asksaveasfilename(
            title="Exporter la compétence en JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile=f"{s.name.replace(' ', '_')}.json",
        )
        if not path:
            return
        try:
            import json
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Exporté", f"Compétence exportée vers:\n{path}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Export impossible:\n{e}")
