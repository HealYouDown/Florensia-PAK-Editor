import os
from io import BytesIO, StringIO
from typing import TYPE_CHECKING, Any

from PIL import Image
from PIL.ImageQt import ImageQt
from PySide6 import QtCore, QtGui, QtWidgets

from pak_editor.parsers.bin_file import parse_bin
from pak_editor.parsers.dat_file import parse_dat
from pak_editor.utils import clear_layout, dump_to_excel, dump_to_json

if TYPE_CHECKING:
    from pak_editor.parsers.pak_file import File


class PreviewTable(QtWidgets.QTableWidget):
    def __init__(self, data: list[dict[str, Any]]) -> None:
        super().__init__()
        self._data = data

        headers = list(data[0].keys())

        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.setColumnCount(len(headers))
        self.setRowCount(len(data) + 1)

        for x, header in enumerate(headers):
            self.setItem(0, x, QtWidgets.QTableWidgetItem(header))

        for y, row in enumerate(data, start=1):
            for x, header in enumerate(headers):
                self.setItem(y, x, QtWidgets.QTableWidgetItem(str(row[header])))

        self.resizeColumnsToContents()

    def _show_context_menu(self, point: QtCore.QPoint) -> None:
        menu = QtWidgets.QMenu()
        save_action = menu.addAction("Save")
        save_action.setIcon(QtGui.QIcon.fromTheme("document-save-as"))
        save_action.triggered.connect(self._export_table)
        menu.exec(self.mapToGlobal(point))

    def _export_table(self) -> None:
        excel_type = "Excel (*.xlsx)"
        json_type = "EUC-KR encoded JSON (*.json)"
        path, type_ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Select save location", filter=";;".join((excel_type, json_type))
        )

        if not path:
            return

        try:
            if type_ == excel_type:
                dump_to_excel(path, self._data)
            elif type_ == json_type:
                dump_to_json(path, self._data)
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Export failed", f"Failed to export file: {str(e)} "
            )


class PreviewWidget(QtWidgets.QScrollArea):
    def __init__(self) -> None:
        super().__init__()
        self.setWidgetResizable(True)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )

        widget = QtWidgets.QWidget()
        self.setWidget(widget)

        self._layout = QtWidgets.QVBoxLayout()
        widget.setLayout(self._layout)

    def preview_file(self, file: "File"):
        name, ext = os.path.splitext(file.name)
        ext = ext.lower()

        self.clear_preview()

        if ext in (".txt", ".xml"):
            # try the first encoding that doesn't error out, no idea what AHA did with some of the files..
            encodings = ("euc_kr", "utf-8", "utf-16", "cp1252")
            for encoding in encodings:
                try:
                    text = file.content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                text = f"Failed to decode text using any of the following encodings: {encodings!r}"

            self._preview_text(text)

        elif ext in (".png", ".jpeg", ".jpg", ".bmp", ".tga", ".dds"):
            image = Image.open(BytesIO(file.content))
            self._preview_image(image)

        elif ext in (".dat", ".bin"):
            try:
                if ext == ".bin":
                    data = parse_bin(BytesIO(file.content))
                elif ext == ".dat":
                    data = parse_dat(StringIO(file.content.decode("cp949")))
            except Exception as e:
                self._preview_text(f"Failed to parse file: {str(e)}")
                return

            self._preview_table(data)  # type: ignore
        else:
            self._preview_text("No preview available")

    def clear_preview(self) -> None:
        clear_layout(self._layout)

    def _preview_text(self, text: str) -> None:
        label = QtWidgets.QLabel(text)
        label.setWordWrap(True)
        label.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.IBeamCursor))
        label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByKeyboard
            | QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._layout.addWidget(label)

    def _preview_image(self, image: Image.Image) -> None:
        qimage = ImageQt(image)
        pixmap = QtGui.QPixmap.fromImage(qimage)

        label = QtWidgets.QLabel()
        label.setPixmap(pixmap)
        self._layout.addWidget(label)

    def _preview_table(self, data: list[dict[str, Any]]) -> None:
        if not data:
            self._preview_text("No rows found in table data")
            return

        try:
            table = PreviewTable(data)
            self._layout.addWidget(table)
        except Exception as e:
            self._preview_text(f"Failed to display table: {str(e)}")
