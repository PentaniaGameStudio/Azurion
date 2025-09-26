# -*- coding: utf-8 -*-
"""
///summary
Fenêtre principale + navigation et menu.
"""
import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional

from .datastore import DataStore
from .ui_create_family import CreateFamilyFrame
from .ui_create_skill import CreateSkillFrame
from .ui_view_skills import ViewSkillsFrame
from .ui_view_families import ViewFamiliesFrame  # ← NOUVEAU

PAD = 8

class MainWindow(tk.Tk):
    def __init__(self, store: DataStore):
        super().__init__()
        self.title("Skill Utility")
        self.geometry("980x660")
        self.minsize(820, 520)
        self.store = store

        self._build_menu()
        self._build_main_buttons()
        self._current_frame: Optional[tk.Frame] = None
        self.show_view_skills()

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Ouvrir un JSON…", command=self._load_other_file)
        file_menu.add_command(label="Exporter JSON sous…", command=self._export_as)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.destroy)
        menubar.add_cascade(label="Fichier", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="À propos", command=self._about)
        menubar.add_cascade(label="Aide", menu=help_menu)
        self.config(menu=menubar)

    def _build_main_buttons(self) -> None:
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=PAD, pady=PAD)

        header = ttk.Label(container, text="Gestion des Compétences", font=("Segoe UI", 16, "bold"))
        header.pack(pady=(0, PAD))

        btns = ttk.Frame(container)
        btns.pack(pady=(0, PAD))

        ttk.Button(btns, text="Créer Famille", width=24, command=self.show_create_family).grid(row=0, column=0, padx=PAD, pady=PAD)
        ttk.Button(btns, text="Créer Compétence", width=24, command=self.show_create_skill).grid(row=0, column=1, padx=PAD, pady=PAD)
        ttk.Button(btns, text="Afficher Compétences", width=24, command=self.show_view_skills).grid(row=0, column=2, padx=PAD, pady=PAD)
        ttk.Button(btns, text="Afficher Familles", width=24, command=self.show_view_families).grid(row=0, column=3, padx=PAD, pady=PAD)  # ← NOUVEAU

        self._frame_host = ttk.Frame(container)
        self._frame_host.pack(fill="both", expand=True)

    def _swap_frame(self, frame: tk.Frame) -> None:
        if hasattr(self, "_current_frame") and self._current_frame is not None:
            self._current_frame.destroy()
        self._current_frame = frame
        self._current_frame.pack(fill="both", expand=True)

    def show_create_family(self) -> None:
        self._swap_frame(CreateFamilyFrame(self._frame_host, self.store))

    def show_create_skill(self) -> None:
        self._swap_frame(CreateSkillFrame(self._frame_host, self.store))

    def show_view_skills(self) -> None:
        self._swap_frame(ViewSkillsFrame(self._frame_host, self.store))

    def show_view_families(self) -> None:  # ← NOUVEAU
        self._swap_frame(ViewFamiliesFrame(self._frame_host, self.store))

    def _load_other_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Ouvrir un JSON",
            filetypes=[("JSON files", "*.json")],
            initialdir=os.path.dirname(self.store.path),
        )
        if not path:
            return
        try:
            self.store = DataStore(path=path)
            self.show_view_skills()
            messagebox.showinfo("Ouvert", f"Fichier chargé:\n{path}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger le fichier:\n{e}")

    def _export_as(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Exporter JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile="skills_data_export.json",
        )
        if not path:
            return
        try:
            payload = {
                "families": [f.__dict__ for f in self.store.families],
                "skills": [s.__dict__ for s in self.store.skills],
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Exporté", f"Données exportées vers:\n{path}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Export impossible:\n{e}")

    def _about(self) -> None:
        messagebox.showinfo(
            "À propos",
            "Skill Utility (multi-fichiers)\n\nCréer des familles, créer des compétences,\n"
            "afficher les compétences et lister les familles.\n\nFichier: skills_data.json (dans le dossier du package)"
        )
