# -*- coding: utf-8 -*-
"""Entry point for the Skill Creator application (Qt edition)."""
from __future__ import annotations

import sys
from PySide6.QtWidgets import QApplication

from Program.datastore import DataStore
from Program.ui_main import MainWindow


def main(custom_path: str | None = None) -> int:
    """Start the Qt application."""
    qt_app = QApplication(sys.argv)
    store = DataStore(path=custom_path) if custom_path else DataStore()
    window = MainWindow(store, qt_app)
    window.show()
    return qt_app.exec()


if __name__ == "__main__":
    custom = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(main(custom_path=custom))
