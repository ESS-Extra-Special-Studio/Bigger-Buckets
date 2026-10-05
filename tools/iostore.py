"""Reads packages out of the game's IoStore container (.utoc/.ucas).

Build 25632050's container is not encrypted. Blocks are compressed with the
method named in the .utoc; Oodle blocks need an Oodle decompressor
(see decompress()). Read-only: never writes to the game folder.

Usage:
  python iostore.py info
  python iostore.py find <regex>
  python iostore.py extract <regex> <outdir>
"""
import os
import re
import struct
import sys

PAKS = r"C:\Program Files (x86)\Steam\steamapps\common\RSDragonwilds\RSDragonwilds\Content\Paks"
UTOC = os.path.join(PAKS, "RSDragonwilds-Windows.utoc")
UCAS = os.path.join(PAKS, "RSDragonwilds-Windows.ucas")


class R:
    def __init__(self, b, o=0):
        self.b, self.o = b, o

    def u8(self):
        v = self.b[self.o]
        self.o += 1
        return v

    def u32(self):
        v = struct.unpack_from("<I", self.b, self.o)[0]
        self.o += 4
        return v

    def i32(self):
        v = struct.unpack_from("<i", self.b, self.o)[0]
        self.o += 4
        return v

    def u64(self):
        v = struct.unpack_from("<Q", self.b, self.o)[0]
        self.o += 8
        return v

    def fstring(self):
        n = self.i32()
        if n == 0:
            return ""
        if n > 0:
            s = self.b[self.o:self.o + n - 1].decode("latin-1")
            self.o += n
        else:
            n = -n
            s = self.b[self.o:self.o + 2 * n - 2].decode("utf-16-le")
            self.o += 2 * n
        return s


def be40(b, o):
    return int.from_bytes(b[o:o + 5], "big")


class Toc:
    def __init__(self, path=UTOC):
        b = open(path, "rb").read()
        r = R(b, 16)
        self.version = r.u8()
        r.o += 3
        hs = r.u32()
        self.entry_count = r.u32()
        self.block_count = r.u32()
        bes = r.u32()
        mc = r.u32()
        ml = r.u32()
        self.block_size = r.u32()
        self.dir_index_size = r.u32()
        self.partition_count = r.u32()
        r.u64()
        r.o += 16
        self.flags = r.u8()
        r.o += 3
        seeds = r.u32()
        self.partition_size = r.u64()
        nohash = r.u32()
        o = hs
        self.chunk_ids = [b[o + i * 12:o + i * 12 + 12] for i in range(self.entry_count)]
        o += self.entry_count * 12
        self.offlen = []
        for i in range(self.entry_count):
            p = o + i * 10
            self.offlen.append((be40(b, p), be40(b, p + 5)))
        o += self.entry_count * 10
        if self.version >= 4:
            o += seeds * 4
        if self.version >= 5:
            o += nohash * 4
        self.blocks = []
        for i in range(self.block_count):
            p = o + i * bes
            off = int.from_bytes(b[p:p + 5], "little")
            csz = int.from_bytes(b[p + 5:p + 8], "little")
            usz = int.from_bytes(b[p + 8:p + 11], "little")
            meth = b[p + 11]
            self.blocks.append((off, csz, usz, meth))
        o += self.block_count * bes
        self.methods = [b[o + i * ml:o + (i + 1) * ml].split(b"\0")[0].decode() for i in range(mc)]
        o += mc * ml
        if self.flags & 4:
            hsz = struct.unpack_from("<i", b, o)[0]
            o += 4 + hsz * 2 + self.block_count * 20
        self.paths = {}
        if self.flags & 2:
            return
        r = R(b, o)
        mount = r.fstring()
        nd = r.u32()
        dirs = [(r.u32(), r.u32(), r.u32(), r.u32()) for _ in range(nd)]
        nf = r.u32()
        files = [(r.u32(), r.u32(), r.u32()) for _ in range(nf)]
        ns = r.u32()
        strings = [r.fstring() for _ in range(ns)]
        none = 0xFFFFFFFF
        stack = [(0, mount)]
        while stack:
            di, prefix = stack.pop()
            name, child, _sib, ff = dirs[di]
            here = prefix + strings[name] + "/" if name != none else prefix
            f = ff
            while f != none:
                fname, nxt, user = files[f]
                self.paths[here + strings[fname]] = user
                f = nxt
            c = child
            while c != none:
                stack.append((c, here))
                c = dirs[c][2]

    def read_chunk(self, idx):
        off, length = self.offlen[idx]
        first = off // self.block_size
        last = (off + length - 1) // self.block_size
        out = bytearray()
        with open(UCAS, "rb") as fh:
            for bi in range(first, last + 1):
                boff, csz, usz, meth = self.blocks[bi]
                fh.seek(boff)
                raw = fh.read((csz + 15) & ~15)[:csz]
                out += decompress(self.methods[meth - 1] if meth else "None", raw, usz)
        start = off - first * self.block_size
        return bytes(out[start:start + length])


_oodle = None


def decompress(method, raw, usz):
    global _oodle
    if method == "None":
        return raw[:usz]
    if method == "Zlib":
        import zlib
        return zlib.decompress(raw)[:usz]
    if method == "Oodle":
        if _oodle is None:
            _oodle = load_oodle()
        return _oodle(raw, usz)
    raise RuntimeError(f"unsupported compression {method}")


def load_oodle():
    """Uses an Oodle DLL named by OODLE_DLL, else the pyooz package."""
    dll = os.environ.get("OODLE_DLL")
    if dll:
        import ctypes
        lib = ctypes.WinDLL(dll)
        fn = lib.OodleLZ_Decompress
        fn.restype = ctypes.c_int64

        def run(raw, usz):
            out = ctypes.create_string_buffer(usz)
            n = fn(raw, ctypes.c_int64(len(raw)), out, ctypes.c_int64(usz),
                   1, 0, 0, None, 0, None, None, None, 0, 3)
            if n != usz:
                raise RuntimeError(f"oodle returned {n}, wanted {usz}")
            return out.raw
        return run
    import ooz  # pyooz
    return lambda raw, usz: ooz.decompress(raw, usz)


def main():
    toc = Toc()
    cmd = sys.argv[1]
    if cmd == "info":
        print(f"version {toc.version} entries {toc.entry_count} blocks {toc.block_count} "
              f"block_size {toc.block_size} flags 0x{toc.flags:X} partitions {toc.partition_count} "
              f"methods {toc.methods} paths {len(toc.paths)}")
        used = {}
        for blk in toc.blocks[:200000]:
            used[blk[3]] = used.get(blk[3], 0) + 1
        print("method usage (first 200k blocks):", used)
    elif cmd == "find":
        pat = re.compile(sys.argv[2], re.I)
        for p, idx in sorted(toc.paths.items()):
            if pat.search(p):
                print(idx, toc.offlen[idx][1], p)
    elif cmd == "extract":
        pat = re.compile(sys.argv[2], re.I)
        outdir = sys.argv[3]
        os.makedirs(outdir, exist_ok=True)
        for p, idx in sorted(toc.paths.items()):
            if pat.search(p):
                data = toc.read_chunk(idx)
                dst = os.path.join(outdir, os.path.basename(p))
                open(dst, "wb").write(data)
                print(len(data), dst)


if __name__ == "__main__":
    main()
