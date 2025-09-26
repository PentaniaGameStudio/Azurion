# -*- coding: utf-8 -*-
"""
///summary
Widgets réutilisables (labels + inputs).
"""
import tkinter as tk
from tkinter import ttk
from typing import List

class LabeledEntry(ttk.Frame):
    def __init__(self, master, label: str, width: int = 40, **kwargs):
        super().__init__(master, **kwargs)
        ttk.Label(self, text=label).pack(anchor="w")
        self.var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.var, width=width)
        self.entry.pack(fill="x")

class LabeledText(ttk.Frame):
    def __init__(self, master, label: str, height: int = 4, **kwargs):
        super().__init__(master, **kwargs)
        ttk.Label(self, text=label + " (1 par ligne)").pack(anchor="w")
        self.text = tk.Text(self, height=height, wrap="word")
        self.text.pack(fill="both", expand=True)
    def get_lines(self) -> List[str]:
        raw = self.text.get("1.0", "end").strip()
        return [line.strip() for line in raw.splitlines() if line.strip()]

# -*- coding: utf-8 -*-
"""
///summary
Frame scrollable verticale (Canvas + Frame) avec molette globale (bind_all)
activée uniquement quand la souris est dans le scrollview, largeur auto.
"""
import tkinter as tk
from tkinter import ttk

class ScrollableFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self._canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0)
        self._vsb = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._inner = ttk.Frame(self._canvas)

        self._window_id = self._canvas.create_window((0, 0), window=self._inner, anchor="nw")
        self._canvas.configure(yscrollcommand=self._vsb.set)

        self._canvas.pack(side="left", fill="both", expand=True)
        self._vsb.pack(side="right", fill="y")

        # Largeur auto + scrollregion
        self._inner.bind("<Configure>", lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        # État : souris à l'intérieur ?
        self._inside = False
        self._wsys = self.tk.call('tk', 'windowingsystem')  # 'win32' / 'aqua' / 'x11'

        # Active/désactive le scroll global quand on ENTRE/SORT
        # → on écoute à la fois le canvas et la frame interne
        for w in (self._canvas, self._inner):
            w.bind("<Enter>", self._on_enter, add="+")
            w.bind("<Leave>", self._on_leave, add="+")

    def _on_canvas_configure(self, event):
        # Forcer la largeur du contenu = largeur visible du canvas
        self._canvas.itemconfigure(self._window_id, width=event.width)

    # --- Gestion entrée/sortie de la zone -----------------------------------
    def _on_enter(self, _evt=None):
        if self._inside:
            return
        self._inside = True
        self._activate_global_wheel()

    def _on_leave(self, _evt=None):
        # Vérifie si la souris est encore sur le canvas/inner; sinon on désactive
        x_root, y_root = self.winfo_pointerxy()
        widget_under = self.winfo_containing(x_root, y_root)
        if widget_under in (self._canvas, self._inner) or self._is_child_of(widget_under, self._inner):
            return
        self._inside = False
        self._deactivate_global_wheel()

    def _is_child_of(self, widget, parent):
        """Retourne True si widget est un descendant de parent."""
        while widget is not None:
            if widget is parent:
                return True
            widget = widget.master
        return False

    # --- Activer/Désactiver bindings globaux de molette ---------------------
    def _activate_global_wheel(self):
        # Bind sur la toplevel (global) pour choper l'événement où qu'il arrive
        top = self.winfo_toplevel()
        if self._wsys in ('win32', 'aqua'):
            top.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
            top.bind_all("<Shift-MouseWheel>", self._on_shift_wheel, add="+")
        else:  # Linux/X11
            top.bind_all("<Button-4>", self._on_button4, add="+")
            top.bind_all("<Button-5>", self._on_button5, add="+")

    def _deactivate_global_wheel(self):
        top = self.winfo_toplevel()
        try:
            if self._wsys in ('win32', 'aqua'):
                top.unbind_all("<MouseWheel>")
                top.unbind_all("<Shift-MouseWheel>")
            else:
                top.unbind_all("<Button-4>")
                top.unbind_all("<Button-5>")
        except Exception:
            pass

    # --- Handlers molette ----------------------------------------------------
    def _on_mousewheel(self, event):
        # Si on a quitté entre temps, ignore
        if not self._inside:
            return
        # Windows: delta multiple de 120 ; macOS: petit delta mais signe identique
        units = int(-event.delta / 120) if event.delta else 0
        if units == 0:
            units = -1 if event.delta > 0 else 1
        self._canvas.yview_scroll(units, "units")

    def _on_shift_wheel(self, event):
        if not self._inside:
            return
        units = int(-event.delta / 120) if event.delta else 0
        if units == 0:
            units = -1 if event.delta > 0 else 1
        self._canvas.xview_scroll(units, "units")

    def _on_button4(self, _event):
        if not self._inside:
            return
        self._canvas.yview_scroll(-1, "units")

    def _on_button5(self, _event):
        if not self._inside:
            return
        self._canvas.yview_scroll(1, "units")

    @property
    def body(self) -> ttk.Frame:
        """Frame interne dans laquelle ajouter les champs."""
        return self._inner
        
        # --- API publique pour geler/dégeler la molette depuis l'extérieur ---
    def suspend_wheel(self):
        """Désactive les bindings globaux de molette (utile quand un popdown est ouvert)."""
        try:
            self._deactivate_global_wheel()
        except Exception:
            pass

    def resume_wheel(self):
        """Réactive les bindings globaux de molette si la souris est encore dans la zone."""
        try:
            # On ne réactive que si le pointeur est dedans (sinon, laisse inactif)
            x_root, y_root = self.winfo_pointerxy()
            widget_under = self.winfo_containing(x_root, y_root)
            if widget_under in (self._canvas, self._inner) or self._is_child_of(widget_under, self._inner):
                self._activate_global_wheel()
        except Exception:
            pass

