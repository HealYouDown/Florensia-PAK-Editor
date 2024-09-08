import json
import os
import sys
from typing import Any

import xlsxwriter as xlsx
from PySide6 import QtWidgets


def clear_layout(layout: QtWidgets.QLayout) -> None:
    # See https://stackoverflow.com/a/25330164
    for i in reversed(range(layout.count())):
        widget = layout.itemAt(i).widget()
        layout.removeWidget(widget)
        widget.setParent(None)


def make_asset_path(*paths) -> str:
    if getattr(sys, "frozen", False):
        # if the application is run as a bundle, the pyinstaller bootloader
        # extends the sys module by a flag frozen=True and sets the apps path into the variable _MEIPASS
        app_path = sys._MEIPASS  # type: ignore
    else:
        root = os.getcwd()
        app_path = os.path.join(root, "pak_editor", "assets")

    return os.path.join(app_path, *paths)


def dump_to_excel(
    filepath: str,
    data: list[dict[str, Any]],
) -> None:
    if not data:
        raise ValueError("Expected at least one dict inside data, got 0")

    wb = xlsx.Workbook(filepath)
    bold = wb.add_format({"bold": True})
    sheet = wb.add_worksheet()

    headers = list(data[0].keys())

    sheet.write_row(0, 0, headers, bold)

    for y, row in enumerate(data, start=1):
        # in case values are in different order, we look them up by the header key
        # it's a small overhead, but ensures order
        sheet.write_row(y, 0, [row[header] for header in headers])

    wb.close()


def dump_to_json(
    filepath: str,
    data: list[dict[str, list | dict | str | int | float | bool | None]],
) -> None:
    if not data:
        raise ValueError("Expected at least one dict inside data, got 0")

    with open(filepath, "w", encoding="euc_kr") as fp:
        json.dump(data, fp, indent=4, ensure_ascii=False)
