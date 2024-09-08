from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui, QtWidgets

from pak_editor.parsers.pak_file import File
from pak_editor.utils import clear_layout

if TYPE_CHECKING:
    from pak_editor.parsers.pak_file import File


class PakFileInfoWidget(QtWidgets.QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._layout = QtWidgets.QGridLayout()
        self.setLayout(self._layout)

        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Maximum,
        )

    def clear_infos(self) -> None:
        clear_layout(self._layout)

    def update_infos(self, file: "File") -> None:
        clear_layout(self._layout)

        values = [
            "Offset:",
            str(file.offset) if file.offset is not None else "/",
            "Length:",
            str(file.length) if file.length is not None else "/",
            "Checksum 1:",
            str(file.checksum_1) if file.checksum_1 is not None else "/",
            "Unknown:",
            file.unknown.hex(sep=" ").upper() if file.unknown else "/",
        ]
        fixed_font = QtGui.QFont("monospace")

        for idx, value in enumerate(values):
            row = idx // 2
            column = idx % 2

            label = QtWidgets.QLabel(value)
            # label.setWordWrap(True) # results in some weird layout shifting when resizing mainwindow
            label.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.IBeamCursor))
            label.setTextInteractionFlags(
                QtCore.Qt.TextInteractionFlag.TextSelectableByKeyboard
                | QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
            )
            if column == 0:
                label.setStyleSheet("font: bold")
                label.setAlignment(
                    QtCore.Qt.AlignmentFlag.AlignRight
                    | QtCore.Qt.AlignmentFlag.AlignVCenter
                )
            elif column == 1:
                label.setSizePolicy(
                    QtWidgets.QSizePolicy.Policy.Expanding,
                    QtWidgets.QSizePolicy.Policy.Preferred,
                )
                label.setFont(fixed_font)

            self._layout.addWidget(label, row, column)
