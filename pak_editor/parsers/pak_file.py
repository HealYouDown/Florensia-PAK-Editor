import os
import struct
from dataclasses import dataclass, field


@dataclass
class File:
    name: str
    content: bytes = field(repr=False)

    # These values that are available when a pak is read, but not when a file is manually created/added.
    # They are not used anywhere and are only informative.
    offset: int | None = field(compare=False, hash=False, default=None)
    length: int | None = field(compare=False, hash=False, default=None)
    checksum_1: int | None = field(compare=False, hash=False, default=None)
    unknown: bytes | None = field(compare=False, hash=False, default=None)

    @classmethod
    def from_path(cls, path: str):
        filename = os.path.basename(path)

        with open(path, "rb") as fp:
            content = fp.read()

        return cls(name=filename, content=content)


@dataclass
class PakFile:
    files: list[File]

    # Same as File attributes above, only informative (used for window title though)
    original_file_name: str | None = field(compare=False, hash=False, default=None)

    @classmethod
    def load(cls, path: str):
        with open(path, "rb") as fp:
            count = struct.unpack("<I", fp.read(4))[0]

            files: list[File] = []
            for _ in range(count):
                name_as_bytes: bytes = struct.unpack("<260s", fp.read(260))[0]
                name = name_as_bytes.decode("ascii").rstrip("\x00")

                offset = struct.unpack("<I", fp.read(4))[0]
                length = struct.unpack("<I", fp.read(4))[0]

                # appears to be the same for some files
                # first 4 bytes are always 2172649504
                # bytes are different when the int values in the version.bin file changes
                unknown = fp.read(24)  # noqa: F841

                # matches first value in version.bin
                # probably used by the launcher to check if a file has changed
                checksum_1 = struct.unpack("<I", fp.read(4))[0]  # noqa: F841

                previous_pos = fp.tell()
                fp.seek(offset)
                content = fp.read(length)
                fp.seek(previous_pos)

                files.append(
                    File(
                        name=name,
                        content=content,
                        offset=offset,
                        length=length,
                        checksum_1=checksum_1,
                        unknown=unknown,
                    )
                )

        filename = os.path.basename(path)
        return cls(files=files, original_file_name=filename)

    def pack(self) -> bytes:
        out = b""
        out += struct.pack("<I", len(self.files))

        # our first offset starts after the file headers
        # each file takes up 260 + 4 + 4 + 24 + 4 bytes of header data
        offset = 4 + ((260 + 4 + 4 + 24 + 4) * len(self.files))

        for file in self.files:
            out += struct.pack("<260s", file.name.encode("ascii"))
            out += struct.pack("<I", offset)
            out += struct.pack("<I", len(file.content))
            out += struct.pack("28x")

            offset += len(file.content)

        for file in self.files:
            out += file.content

        return out
