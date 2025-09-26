# -*- coding: utf-8 -*-
"""
///summary
Point d'entrée de l'application GUI.
"""
import sys
from Program.datastore import DataStore
from Program.ui_main import MainWindow

def main(custom_path=None):
    store = DataStore(path=custom_path) if custom_path else DataStore()
    app = MainWindow(store)
    app.mainloop()

if __name__ == "__main__":
    custom = sys.argv[1] if len(sys.argv) > 1 else None
    main(custom_path=custom)
