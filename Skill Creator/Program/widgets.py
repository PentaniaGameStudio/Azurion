# -*- coding: utf-8 -*-
"""Reusable Qt widgets for the Skill Creator application."""
from __future__ import annotations

from typing import List

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit


class LabeledLineEdit(QWidget):
    """Simple widget combining a label and a line edit."""

    def __init__(self, label: str, width: int | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._label = QLabel(label)
        layout.addWidget(self._label)

        self._line = QLineEdit()
        if width:
            self._line.setMaximumWidth(width * 8)
        layout.addWidget(self._line)

    def text(self) -> str:
        return self._line.text()

    def setText(self, value: str) -> None:  # noqa: N802 (Qt naming convention)
        self._line.setText(value)

    def set_label_visible(self, visible: bool) -> None:
        self._label.setVisible(visible)

    def setPlaceholderText(self, text: str) -> None:
        self._line.setPlaceholderText(text)


class LabeledTextEdit(QWidget):
    """Widget combining a label and a QTextEdit with helper methods."""

    def __init__(self, label: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._label = QLabel(f"{label} (1 par ligne)")
        layout.addWidget(self._label)

        self._text = QTextEdit()
        self._text.setAcceptRichText(False)
        layout.addWidget(self._text)

    def get_lines(self) -> List[str]:
        raw = self._text.toPlainText().strip()
        return [line.strip() for line in raw.splitlines() if line.strip()]

    def clear(self) -> None:
        self._text.clear()

    def setPlainText(self, text: str) -> None:
        self._text.setPlainText(text)

    def toPlainText(self) -> str:
        return self._text.toPlainText()
