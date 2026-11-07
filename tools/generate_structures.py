"""Writes GameTest structure templates (gzipped NBT) used by the native tests.

`platform`: 15 x 10 x 15 with a stone floor at y=0 and air above. The tests build what they need on it,
including the Ice and Fire forge, so no third-party block ids are frozen into a binary template.
"""
from pathlib import Path
import gzip
import struct

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src/gametest/resources/data/dragonsteel_schools/structures"
DATA_VERSION = 3465  # Minecraft 1.20.1


def tag_header(tag_type: int, name: str) -> bytes:
    raw = name.encode("utf-8")
    return struct.pack(">bH", tag_type, len(raw)) + raw


def string_payload(value: str) -> bytes:
    raw = value.encode("utf-8")
    return struct.pack(">H", len(raw)) + raw


def int_list(name: str, values) -> bytes:
    return tag_header(9, name) + struct.pack(">bi", 3, len(values)) + b"".join(struct.pack(">i", v) for v in values)


def compound_list(name: str, compounds) -> bytes:
    return tag_header(9, name) + struct.pack(">bi", 10, len(compounds)) + b"".join(c + b"\x00" for c in compounds)


def platform(size_x: int, size_y: int, size_z: int) -> bytes:
    palette = [tag_header(8, "Name") + string_payload("minecraft:stone"),
               tag_header(8, "Name") + string_payload("minecraft:air")]
    blocks = []
    for x in range(size_x):
        for y in range(size_y):
            for z in range(size_z):
                state = 0 if y == 0 else 1
                blocks.append(tag_header(3, "state") + struct.pack(">i", state) + int_list("pos", [x, y, z]))
    body = (tag_header(3, "DataVersion") + struct.pack(">i", DATA_VERSION)
            + int_list("size", [size_x, size_y, size_z])
            + compound_list("palette", palette)
            + compound_list("blocks", blocks)
            + compound_list("entities", []))
    return tag_header(10, "") + body + b"\x00"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / "platform.nbt"
    with gzip.GzipFile(target, "wb", mtime=0) as handle:
        handle.write(platform(15, 10, 15))
    print(f"wrote {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
