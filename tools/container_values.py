"""Reads Capacity, AmountDischargedPerUse and PlotDischargeMultiplier from
cooked ITEM_* container assets (unversioned zen export data, UE 5.6).

Schema order comes from the exe's reflection data (reflect_props.py): the
most-derived class's properties are indices 0..6:
  0 Capacity (int32), 1 AmountDischargedPerUse (int32),
  2 PlotDischargeMultiplier (float), 3 AllowedFillTypes (array),
  4-6 Container{Empty,Some,Full}ContentsDescription (text).
An index missing from the header means the asset keeps the C++ default.

Usage: python container_values.py <ITEM_*.uasset> [...]
"""
import struct
import sys

sys.path.insert(0, __file__.rsplit("\\", 1)[0])
from zen_names import names  # noqa: E402


def fragments(b, o):
    present, zero_flagged = [], []
    idx = 0
    while True:
        f = struct.unpack_from("<H", b, o)[0]
        o += 2
        skip, has_zero, last, num = f & 0x7F, (f >> 7) & 1, (f >> 8) & 1, f >> 9
        idx += skip
        for _ in range(num):
            present.append(idx)
            if has_zero:
                zero_flagged.append(idx)
            idx += 1
        if last:
            break
    zero = set()
    if zero_flagged:
        n = len(zero_flagged)
        nbytes = 1 if n <= 8 else ((n + 31) // 32) * 4
        mask = int.from_bytes(b[o:o + nbytes], "little")
        o += nbytes
        for i, p in enumerate(zero_flagged):
            if mask >> i & 1:
                zero.add(p)
    return present, zero, o


def main():
    print(f"{'asset':28} {'Capacity':>8} {'Discharge':>9} {'PlotMult':>9}")
    for path in sys.argv[1:]:
        b = open(path, "rb").read()
        _nm, hs = names(b)
        present, zero, o = fragments(b, hs)
        vals = {}
        for idx in (0, 1, 2):
            if idx not in present:
                vals[idx] = "default"
            elif idx in zero:
                vals[idx] = 0
            else:
                fmt = "<f" if idx == 2 else "<i"
                vals[idx] = struct.unpack_from(fmt, b, o)[0]
                o += 4
        name = path.replace("\\", "/").rsplit("/", 1)[-1]
        print(f"{name:28} {vals[0]!s:>8} {vals[1]!s:>9} {vals[2]!s:>9}   present={present[:10]}...")


if __name__ == "__main__":
    main()
