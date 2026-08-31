#!/usr/bin/env python3
"""rominfo.py — 顯示 Super A'Can ROM 基本資訊（68k 向量表、入口點）。

自動做 word-swap 還原後讀取向量表（見 docs/bios-rom-format.md、docs/memory-map.md）。
卡帶授權區（$2000 起 128 bytes，類 TMSS）也會一併檢查。

用法：
    rominfo.py game.bin
"""
import hashlib
import struct
import sys
from pathlib import Path


def deswap(data: bytes) -> bytes:
    out = bytearray(data)
    for i in range(0, len(out) - 1, 2):
        out[i], out[i + 1] = out[i + 1], out[i]
    return bytes(out)


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    raw = Path(sys.argv[1]).read_bytes()
    rom = deswap(raw)
    print(f"size        : {len(raw)} bytes ({len(raw) // 1024} KiB)")
    print(f"sha256(raw) : {hashlib.sha256(raw).hexdigest()}")
    if len(rom) < 8:
        print("檔案太小，無向量表")
        return 1
    ssp, pc = struct.unpack(">II", rom[:8])
    print(f"initial SSP : ${ssp:08X}")
    print(f"entry PC    : ${pc:08X}")
    if len(rom) >= 0x2080:
        lic = rom[0x2000:0x2080]
        print(f"data @$2000 : {lic[:16].hex(' ')} ...（128 bytes，IPL 授權比對區，見 docs/bios-68k.md §4）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
