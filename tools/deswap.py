#!/usr/bin/env python3
"""deswap.py — Super A'Can ROM/BIOS 16-bit word-swap 轉換。

ROM 與 internal_68k.bin 在檔案中是 byte-swapped 格式（見 docs/bios-rom-format.md）。
本工具把每個 16-bit word 的兩個 byte 對調，還原為 68k 原生位元組序（或反向轉換，操作對稱）。

用法：
    deswap.py in.bin out.bin
"""
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 1
    data = bytearray(Path(sys.argv[1]).read_bytes())
    if len(data) % 2:
        print("warning: 檔案長度為奇數，最後一個 byte 原樣保留", file=sys.stderr)
    for i in range(0, len(data) - 1, 2):
        data[i], data[i + 1] = data[i + 1], data[i]
    Path(sys.argv[2]).write_bytes(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
