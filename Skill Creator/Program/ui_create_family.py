# -*- coding: utf-8 -*-
"""
///summary
Formulaire: Créer Famille (sans description, conserve les émojis après enregistrement).
"""
import tkinter as tk
from tkinter import ttk, messagebox
from .datastore import DataStore
from .models import Family
from .widgets import LabeledEntry

PAD = 8

class CreateFamilyFrame(ttk.Frame):
    def __init__(self, master, store: DataStore):
        super().__init__(master, padding=PAD)
        self.store = store

        ttk.Label(self, text="Créer une Famille", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, PAD))

        self.emojis = LabeledEntry(self, "Emojis (clé) — ex: 🌊🔊", width=30)
        self.name = LabeledEntry(self, "Nom de la famille", width=40)

        self.emojis.pack(fill="x", pady=(0, PAD))
        self.name.pack(fill="x", pady=(0, PAD))

        btns = ttk.Frame(self)
        btns.pack(pady=(PAD, 0))
        ttk.Button(btns, text="Enregistrer", command=self._save).grid(row=0, column=0, padx=PAD)
        ttk.Button(btns, text="Annuler", command=self._clear_all).grid(row=0, column=1, padx=PAD)

    # ///summary: Vide le nom uniquement (garde les émojis).
    def _clear_keep_emojis(self) -> None:
        self.name.var.set("")

    # ///summary: Vide tous les champs.
    def _clear_all(self) -> None:
        self.emojis.var.set("")
        self.name.var.set("")

    def _save(self) -> None:
        emojis = self.emojis.var.get().strip()
        name = self.name.var.get().strip()

        if not emojis:
            messagebox.showwarning("Champ requis", "Les emojis (clé) sont obligatoires.")
            return
        try:
            # description non utilisée -> vide
            self.store.add_family(Family(emojis=emojis, name=name, description=""))
            messagebox.showinfo("OK", f"Famille '{emojis}' ajoutée.")
            self._clear_keep_emojis()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
