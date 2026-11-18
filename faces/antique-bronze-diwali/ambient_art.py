#!/usr/bin/env python3
"""Generate and inspect the sparse, 450px ambient artwork using only Python."""
from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).parent
DRAWABLE = ROOT / "src/main/res/drawable"
SOURCE = DRAWABLE / "bronze_dial.png"
AMBIENT = ROOT / "src/main/res/drawable-nodpi/bronze_dial_ambient.png"
STAT_REGION = (60, 200, 390, 295)


def read_rgb_png(path):
    """Read a non-interlaced, 8-bit RGB PNG, including all PNG row filters."""
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Not a PNG: {path}")
    offset = 8
    compressed = bytearray()
    while offset < len(data):
        length = struct.unpack_from(">I", data, offset)[0]
        kind = data[offset + 4:offset + 8]
        chunk = data[offset + 8:offset + 8 + length]
        offset += length + 12
        if kind == b"IHDR":
            width, height, depth, color, compression, filtering, interlace = struct.unpack(
                ">IIBBBBB", chunk
            )
            if (depth, color, compression, filtering, interlace) != (8, 2, 0, 0, 0):
                raise ValueError(f"Expected a non-interlaced 8-bit RGB PNG: {path}")
        elif kind == b"IDAT":
            compressed.extend(chunk)
        elif kind == b"IEND":
            break
    raw = zlib.decompress(compressed)
    stride = width * 3
    previous = bytearray(stride)
    rows = []
    for y in range(height):
        start = y * (stride + 1)
        filter_type = raw[start]
        row = bytearray(raw[start + 1:start + 1 + stride])
        for i in range(stride):
            left = row[i - 3] if i >= 3 else 0
            above = previous[i]
            upper_left = previous[i - 3] if i >= 3 else 0
            if filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = above
            elif filter_type == 3:
                predictor = (left + above) // 2
            elif filter_type == 4:
                p = left + above - upper_left
                distances = (abs(p - left), abs(p - above), abs(p - upper_left))
                predictor = (left, above, upper_left)[distances.index(min(distances))]
            elif filter_type == 0:
                predictor = 0
            else:
                raise ValueError(f"Unsupported PNG filter: {filter_type}")
            row[i] = (row[i] + predictor) & 255
        rows.append(row)
        previous = row
    return width, height, rows


def write_rgb_png(path, width, height, rows):
    def chunk(kind, data):
        return (struct.pack(">I", len(data)) + kind + data
                + struct.pack(">I", zlib.crc32(kind + data)))

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    pixels = b"".join(b"\x00" + bytes(row) for row in rows)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
                     + chunk(b"IDAT", zlib.compress(pixels, 9)) + chunk(b"IEND", b""))


def generate():
    width, height, source = read_rgb_png(SOURCE)
    size = 450
    rows = []
    left, top, right, bottom = STAT_REGION
    for y in range(size):
        row = bytearray(size * 3)
        for x in range(size):
            sx, sy = x * width // size, y * height // size
            r, g, b = source[sy][sx * 3:sx * 3 + 3]
            # The interactive background contains empty stat rings and dividers.
            in_stat_region = left <= x < right and top <= y < bottom
            if not in_stat_region and r >= 180 and g >= 75:
                row[x * 3:x * 3 + 3] = bytes((r // 2, g // 2, b // 2))
        rows.append(row)
    AMBIENT.parent.mkdir(parents=True, exist_ok=True)
    write_rgb_png(AMBIENT, size, size, rows)


if __name__ == "__main__":
    generate()
