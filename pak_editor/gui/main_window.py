import os
import tempfile
from typing import TYPE_CHECKING, cast

import humanize
import humanize.filesize
from PySide6 import QtCore, QtGui, QtWidgets

from pak_editor.constants import WINDOW_TITLE
from pak_editor.parsers.pak_file import File, PakFile
from pak_editor.utils import make_asset_path

from .file_list_widget import FileListWidget, PakListWidgetItem
from .pak_file_info_widget import PakFileInfoWidget
from .preview_widget import PreviewWidget

if TYPE_CHECKING:
    from pak_editor.parsers.pak_file import File


class PakEditorApp(QtWidgets.QMainWindow):
    pak_changed = QtCore.Signal(PakFile)

    def __init__(self):
        super().__init__()
        self.setMinimumSize(800, 500)
        self.setAcceptDrops(True)

        self.setWindowIcon(QtGui.QIcon(make_asset_path("icon.png")))

        self._pak_file = None

        self.pak_changed.connect(self._update_window_title)
        self.pak_changed.connect(self._update_status_bar)

        menu_bar = QtWidgets.QMenuBar()
        self.setMenuBar(menu_bar)

        file_section = menu_bar.addMenu("File")

        new_action = file_section.addAction("New")
        new_action.setIcon(QtGui.QIcon.fromTheme("document-new"))
        new_action.triggered.connect(self._create_new_pak_file)

        open_action = file_section.addAction("Open")
        open_action.setIcon(QtGui.QIcon.fromTheme("document-open"))
        open_action.triggered.connect(self._ask_open_pak_file)

        close_action = file_section.addAction("Close")
        close_action.setIcon(QtGui.QIcon.fromTheme("edit-clear"))
        close_action.triggered.connect(self._close_pak_file)

        save_as_action = file_section.addAction("Save as")
        save_as_action.setIcon(QtGui.QIcon.fromTheme("document-save-as"))
        save_as_action.triggered.connect(self._save_pak_file)

        file_section.addSeparator()

        exit_action = file_section.addAction("Exit")
        exit_action.setIcon(QtGui.QIcon.fromTheme("application-exit"))
        exit_action.triggered.connect(self._exit_app)

        export_section = menu_bar.addMenu("Export")

        export_selected_files_action = export_section.addAction("Export selected files")
        export_selected_files_action.setIcon(QtGui.QIcon.fromTheme("folder"))
        export_selected_files_action.triggered.connect(self._export_selected_files)

        export_all_files_action = export_section.addAction("Export all files")
        export_all_files_action.setIcon(QtGui.QIcon.fromTheme("emblem-downloads"))
        export_all_files_action.triggered.connect(self._export_all_files)

        self._status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self._status_bar)

        # will be added / shown once a pak file is loaded
        self._status_bar_file_count_label = QtWidgets.QLabel()
        self._status_bar_filesize_label = QtWidgets.QLabel()

        main_splitter = QtWidgets.QSplitter()
        self.setCentralWidget(main_splitter)

        self._file_list_widget = FileListWidget()
        self._file_list_widget.currentItemChanged.connect(
            self._on_file_list_item_changed
        )
        self._file_list_widget.itemDoubleClicked.connect(
            lambda item: self._open_pak_content_file_with_default_app(
                cast(PakListWidgetItem, item).file
            )
        )
        self._file_list_widget.customContextMenuRequested.connect(
            self._on_file_list_context_menu
        )
        self.pak_changed.connect(self._file_list_widget.update_pak_data)
        main_splitter.addWidget(self._file_list_widget)

        vertical_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        main_splitter.addWidget(vertical_splitter)

        self._preview_widget = PreviewWidget()
        vertical_splitter.addWidget(self._preview_widget)

        self._info_widget = PakFileInfoWidget()
        vertical_splitter.addWidget(self._info_widget)

        # forces 50/50 split for splitter
        main_splitter.setSizes([2**31 - 1, 2**31 - 1])

    def _update_status_bar(self, pak_file: PakFile | None) -> None:
        if pak_file is None:
            self._status_bar.removeWidget(self._status_bar_file_count_label)
            self._status_bar.removeWidget(self._status_bar_filesize_label)
            return

        self._status_bar.addWidget(self._status_bar_file_count_label)
        self._status_bar.addWidget(self._status_bar_filesize_label)
        self._status_bar_file_count_label.show()
        self._status_bar_filesize_label.show()

        self._status_bar_file_count_label.setText(f"{len(pak_file.files)} file(s)")

        total_file_size = sum([len(file.content) for file in pak_file.files])
        self._status_bar_filesize_label.setText(
            humanize.filesize.naturalsize(total_file_size, binary=False)
        )

    def _update_window_title(self, pak_file: PakFile | None) -> None:
        if pak_file is None or pak_file.original_file_name is None:
            self.setWindowTitle(WINDOW_TITLE)
            return

        title = f"{WINDOW_TITLE} - {pak_file.original_file_name}"
        self.setWindowTitle(title)

    def _on_file_list_item_changed(
        self,
        new_item: PakListWidgetItem | None,
        previous: PakListWidgetItem | None,
    ) -> None:
        if new_item is None:
            self._info_widget.clear_infos()
            self._preview_widget.clear_preview()
        else:
            file = new_item.file

            self._info_widget.update_infos(file)
            self._preview_widget.preview_file(file)

    def _on_file_list_context_menu(self, point: QtCore.QPoint) -> None:
        if self._pak_file is None:
            return

        files = self._file_list_widget.get_selected_files()
        if not files:
            return

        is_multiple_files = len(files) > 1

        menu = QtWidgets.QMenu()

        def open_action() -> None:
            for file in files:
                self._open_pak_content_file_with_default_app(file)

        open_file = menu.addAction(
            "Open files externally" if is_multiple_files else "Open externally"
        )
        open_file.setIcon(QtGui.QIcon.fromTheme("go-up"))
        open_file.triggered.connect(open_action)

        export_file = menu.addAction("Export files" if is_multiple_files else "Export")
        export_file.setIcon(QtGui.QIcon.fromTheme("folder"))
        export_file.triggered.connect(self._export_selected_files)

        menu.addSeparator()

        def delete_action() -> None:
            assert self._pak_file is not None
            for file in files:
                self._pak_file.files.remove(file)
            self.pak_changed.emit(self._pak_file)

        delete_file = menu.addAction("Delete files" if is_multiple_files else "Delete")
        delete_file.setIcon(QtGui.QIcon.fromTheme("edit-delete"))
        delete_file.triggered.connect(delete_action)

        menu.exec(self.mapToGlobal(point))

    def _exit_app(self) -> None:
        app = QtWidgets.QApplication.instance()
        if app is not None:
            app.quit()

    def _create_new_pak_file(self) -> None:
        self._pak_file = PakFile(files=[])
        self.pak_changed.emit(self._pak_file)

    def _ask_open_pak_file(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select .pak file", filter="PAK (*.pak);;All files (*.*)"
        )
        if path:
            self.load_pak_file(path)

    def _close_pak_file(self):
        self._pak_file = None
        self.pak_changed.emit(self._pak_file)

    def _save_pak_file(self) -> None:
        if self._pak_file is None:
            QtWidgets.QMessageBox.warning(
                self,
                "Error saving pak file",
                "There is currently no active PAK file opened.",
            )
            return

        if not self._pak_file.files:
            QtWidgets.QMessageBox.warning(
                self,
                "Error saving pak file",
                "PAK file has no content",
            )
            return

        save_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, caption="Select save location", filter="PAK (*.pak)"
        )
        if not save_path:
            return

        with open(save_path, "wb") as fp:
            fp.write(self._pak_file.pack())

        QtWidgets.QMessageBox.information(
            self,
            "Saved successfully",
            f"PAK file was saved successfully to {save_path!r}",
        )

    def _open_pak_content_file_with_default_app(self, file: "File") -> None:
        with tempfile.TemporaryDirectory(
            prefix="florensia-pak-editor-",
            delete=False,
        ) as tempdir:
            tmp_filepath = os.path.join(tempdir, file.name)

            with open(tmp_filepath, "wb") as fp:
                fp.write(file.content)

            os.startfile(tmp_filepath)

    def _export_selected_files(self) -> None:
        if self._pak_file is None:
            QtWidgets.QMessageBox.warning(
                self, "Error exporting files", "No PAK file opened"
            )
            return

        selected_files = self._file_list_widget.get_selected_files()
        if not selected_files:
            QtWidgets.QMessageBox.warning(
                self, "Error exporting files", "No files to export selected"
            )
            return

        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select an export folder"
        )
        if not path:
            return

        for file in selected_files:
            with open(os.path.join(path, file.name), "wb") as fp:
                fp.write(file.content)

        QtWidgets.QMessageBox.information(
            self,
            "File export",
            f"{len(selected_files)} file(s) exported successfully to {path!r}",
        )

    def _export_all_files(self) -> None:
        self._file_list_widget.selectAll()
        self._export_selected_files()

    def load_pak_file(self, path: str) -> None:
        try:
            self._pak_file = PakFile.load(path)
        except Exception as e:
            self._pak_file = None
            QtWidgets.QMessageBox.critical(self, "Error reading .pak file", str(e))
        self.pak_changed.emit(self._pak_file)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        if self._pak_file is not None and event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        if self._pak_file is None:
            event.ignore()
            return

        urls = event.mimeData().urls()
        new_files: list[File] = [File.from_path(url.toLocalFile()) for url in urls]
        new_filenames = [f.name for f in new_files]

        for file in self._pak_file.files:
            if file.name in new_filenames:
                self._pak_file.files.remove(file)

        self._pak_file.files.extend(new_files)
        self.pak_changed.emit(self._pak_file)
