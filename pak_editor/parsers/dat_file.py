from typing import Any, TextIO


def parse_dat(fp: TextIO) -> list[dict[str, Any]]:
    lines = [line.strip() for line in fp.readlines()]

    headers = [line.strip() for line in lines[0].split("\t")]
    data_lines = lines[1:-1]

    rows = [[val.strip() for val in line.strip().split("\t")] for line in data_lines]

    return [{header: value for header, value in zip(headers, row)} for row in rows]
