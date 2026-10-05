"""Prints the ASCII strings stored next to each hit in the shipping exe.

UE reflection data keeps a class's property and function names close
together, so neighbours of a known name hint at its siblings. A hit proves
the name exists in this build, not what it does. Read-only.

Usage: python exe_context.py <regex> [radius_bytes]
"""
import re
import sys

EXE = r"C:\Program Files (x86)\Steam\steamapps\common\RSDragonwilds\RSDragonwilds\Binaries\Win64\RSDragonwilds-Win64-Shipping.exe"


def main():
    pat = re.compile(sys.argv[1].encode())
    radius = int(sys.argv[2]) if len(sys.argv) > 2 else 600
    data = open(EXE, "rb").read()
    for m in pat.finditer(data):
        lo, hi = max(0, m.start() - radius), m.end() + radius
        words = [w.decode() for w in re.findall(rb"[A-Za-z_][ -~]{3,120}", data[lo:hi])]
        print(f"== 0x{m.start():x} {m.group().decode(errors='replace')}")
        print("   " + " | ".join(words))


if __name__ == "__main__":
    main()
