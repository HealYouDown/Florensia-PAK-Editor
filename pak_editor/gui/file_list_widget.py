from typing import cast

from PySide6 import QtCore, QtWidgets

from pak_editor.parsers.pak_file import File, PakFile


class PakListWidgetItem(QtWidgets.QListWidgetItem):
    def __init__(self, file: File) -> None:
        super().__init__(file.name)
        self._file = file

    @property
    def file(self) -> File:
        return self._file


class FileListWidget(QtWidgets.QListWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.itemSelectionChanged.connect(self.get_selected_files)

    def update_pak_data(self, pak: PakFile | None) -> None:
        self.clear()

        if pak is None:
            return

        for file in pak.files:
            item = PakListWidgetItem(file)
            self.addItem(item)

    def get_selected_files(self) -> list[File]:
        return [
            item.file for item in cast(list[PakListWidgetItem], self.selectedItems())
        ]
