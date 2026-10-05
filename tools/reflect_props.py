"""Lists a native class's reflected properties from the shipping exe.

Starts from one known property name, finds the FPropertyParams record whose
first field points at that name, then the class's PropPointers array that
points at the record, and prints the name each neighbouring record points
at. Those are the class's UPROPERTYs in declaration order, with their
EPropertyGenFlags type and member offset. The owner is named by following
the FClassParams NoRegister function into StaticClass and reading the wide
strings it passes (class name, then package). Read-only.

Usage: python reflect_props.py <KnownPropertyName> [...]
"""
import struct
import sys

EXE = r"C:\Program Files (x86)\Steam\steamapps\common\RSDragonwilds\RSDragonwilds\Binaries\Win64\RSDragonwilds-Win64-Shipping.exe"


class PE:
    def __init__(self, data):
        self.d = data
        pe = struct.unpack_from("<I", data, 0x3C)[0]
        nsec = struct.unpack_from("<H", data, pe + 6)[0]
        optsz = struct.unpack_from("<H", data, pe + 20)[0]
        opt = pe + 24
        self.base = struct.unpack_from("<Q", data, opt + 24)[0]
        self.secs = []
        s = opt + optsz
        for i in range(nsec):
            name = data[s:s + 8].rstrip(b"\0").decode()
            vsz, va, rsz, raw = struct.unpack_from("<IIII", data, s + 8)
            self.secs.append((name, va, vsz, raw, rsz))
            s += 40

    def off2va(self, off):
        for _n, va, _vsz, raw, rsz in self.secs:
            if raw <= off < raw + rsz:
                return self.base + va + (off - raw)
        return None

    def va2off(self, v):
        rva = v - self.base
        for _n, va, vsz, raw, rsz in self.secs:
            if va <= rva < va + max(vsz, rsz):
                o = raw + (rva - va)
                return o if o < raw + rsz else None
        return None

    def cstr(self, v):
        o = self.va2off(v)
        if o is None:
            return None
        end = self.d.find(b"\0", o, o + 200)
        if end < 0:
            return None
        s = self.d[o:end]
        if not s or any(c < 0x20 or c > 0x7E for c in s):
            return None
        return s.decode()

    def find_ptrs(self, v):
        needle = struct.pack("<Q", v)
        out, i = [], self.d.find(needle)
        while i >= 0:
            out.append(i)
            i = self.d.find(needle, i + 1)
        return out


def record_name(pe, rec_va):
    o = pe.va2off(rec_va)
    if o is None:
        return None
    return pe.cstr(struct.unpack_from("<Q", pe.d, o)[0])


GEN = ["Byte", "Int8", "Int16", "Int", "Int64", "UInt16", "UInt32", "UInt64", "UnsizedInt",
       "UnsizedUInt", "Float", "Double", "Bool", "SoftClass", "WeakObject", "LazyObject",
       "SoftObject", "Class", "Object", "Interface", "Name", "Str", "Array", "Map", "Set",
       "Struct", "Delegate", "InlineMulticastDelegate", "SparseMulticastDelegate", "Text",
       "Enum", "FieldPath", "LWCReal", "Optional"]


def record_info(pe, rec_va):
    o = pe.va2off(rec_va)
    raw = pe.d[o:o + 56]
    gen = raw[24] & 0x3F
    offset = struct.unpack_from("<H", raw, 50)[0]
    return f"{GEN[gen] if gen < len(GEN) else gen}@0x{offset:x}"


def wstr(pe, v):
    o = pe.va2off(v)
    if o is None:
        return None
    end = o
    while end < o + 400 and pe.d[end:end + 2] != b"\0\0":
        end += 2
    try:
        s = pe.d[o:end].decode("utf-16-le")
    except UnicodeDecodeError:
        return None
    return s if s and all(32 <= ord(c) < 127 for c in s) else None


def code_wstrs(pe, va, depth=0, seen=None):
    """Wide strings loaded by lea in a function and the calls it makes first."""
    seen = seen if seen is not None else set()
    if va in seen or depth > 2:
        return []
    seen.add(va)
    o = pe.va2off(va)
    if o is None:
        return []
    code, out = pe.d[o:o + 160], []
    for i in range(len(code) - 7):
        if code[i] in (0x48, 0x4C) and code[i + 1] == 0x8D and (code[i + 2] & 0xC7) == 0x05:
            s = wstr(pe, va + i + 7 + struct.unpack_from("<i", code, i + 3)[0])
            if s:
                out.append(s)
        if code[i] in (0xE8, 0xE9) and i < 40:
            out += code_wstrs(pe, va + i + 5 + struct.unpack_from("<i", code, i + 1)[0], depth + 1, seen)
    return out


def owner(pe, array_va):
    for ref in pe.find_ptrs(array_va):
        no_register = struct.unpack_from("<Q", pe.d, ref - 40)[0]
        names = code_wstrs(pe, no_register)
        if names:
            return " ".join(names[:2])
    return "UNKNOWN"


def main():
    data = open(EXE, "rb").read()
    pe = PE(data)
    for known in sys.argv[1:]:
        print(f"##### {known}")
        i = data.find(b"\0" + known.encode() + b"\0")
        while i >= 0:
            name_va = pe.off2va(i + 1)
            for rec_off in pe.find_ptrs(name_va):
                rec_va = pe.off2va(rec_off)
                for arr_off in pe.find_ptrs(rec_va):
                    lo = arr_off
                    while True:
                        p = struct.unpack_from("<Q", data, lo - 8)[0]
                        if record_name(pe, p) is None:
                            break
                        lo -= 8
                    hi = arr_off
                    while True:
                        p = struct.unpack_from("<Q", data, hi + 8)[0]
                        if record_name(pe, p) is None:
                            break
                        hi += 8
                    names = []
                    for o in range(lo, hi + 8, 8):
                        p = struct.unpack_from("<Q", data, o)[0]
                        names.append(f"{record_name(pe, p)} ({record_info(pe, p)})")
                    print(f"  owner: {owner(pe, pe.off2va(lo))}")
                    print(f"  array @0x{lo:x} ({len(names)} props): " + ", ".join(names))
            i = data.find(b"\0" + known.encode() + b"\0", i + 1)


if __name__ == "__main__":
    main()
