"""Prints the name map and export data of cooked zen packages (UE 5.6).

The name map lists every property, class and object name the asset uses.
Export data is unversioned, so values are shown raw (hex plus candidate
int32/float readings); match them to properties by order, not by guess.

Usage: python zen_names.py <file.uasset> [...]
"""
import struct
import sys


def names(b):
    has_ver, header_size = struct.unpack_from("<II", b, 0)
    o = 4 + 4 + 8 + 4 + 4 + 4 * 9
    if has_ver:
        o += 4  # zen version
        o += 8  # package file version ue4/ue5
        o += 4  # licensee version
        n = struct.unpack_from("<i", b, o)[0]
        o += 4 + n * 20  # custom versions (guid + int)
    count = struct.unpack_from("<I", b, o)[0]
    o += 4
    if count == 0:
        return [], header_size
    o += 4  # string bytes
    o += 8  # hash version
    o += 8 * count
    lens = []
    for i in range(count):
        h = struct.unpack_from(">H", b, o + 2 * i)[0]
        lens.append((bool(h & 0x8000), h & 0x7FFF))
    o += 2 * count
    out = []
    for wide, n in lens:
        if wide:
            if o % 2:
                o += 1
            out.append(b[o:o + 2 * n].decode("utf-16-le"))
            o += 2 * n
        else:
            out.append(b[o:o + n].decode("latin-1"))
            o += n
    return out, header_size


def main():
    for path in sys.argv[1:]:
        b = open(path, "rb").read()
        nm, hs = names(b)
        print(f"===== {path}  size {len(b)} header {hs}")
        for i, n in enumerate(nm):
            print(f"  [{i}] {n}")
        body = b[hs:]
        print(f"  export bytes {len(body)}:")
        for o in range(0, len(body), 16):
            chunk = body[o:o + 16]
            ints = [struct.unpack_from("<i", chunk, k)[0] for k in range(0, len(chunk) - 3, 4)]
            flts = [struct.unpack_from("<f", chunk, k)[0] for k in range(0, len(chunk) - 3, 4)]
            print(f"   {o:5x}: {chunk.hex(' '):<48} i{ints} f{[round(x, 3) for x in flts]}")


if __name__ == "__main__":
    main()
