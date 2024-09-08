import sys

from PySide6 import QtWidgets

from pak_editor import PakEditorApp

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = PakEditorApp()
    window.show()

    if len(sys.argv) >= 2:
        window.load_pak_file(sys.argv[1])

    app.exec()
