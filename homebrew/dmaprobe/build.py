#!/usr/bin/env python3
"""建置主機 DMA control 位元的測試卡帶。

每個案例把同一份 64 byte 來源搬進自己的 256 byte 目的區（起點在區塊中央，因此遞減
方向也不會踩到隔壁），再把六個 DMA 暫存器讀回另一塊 VRAM。畫面用 8bpp tilemap 顯示
這兩塊，一個 byte 就是一個像素，截圖可以逐 byte 反推行為。
"""
import argparse, os, struct, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, "build")
ROM_SIZE = 0x80000
AUTH_OFFSET, AUTH_SIZE = 0x2000, 0x400
PATTERN_ADDR = 0x3000           # ROM 內的來源樣本位址
VRAM_BASE = 0x00F40000
COUNT = 15                      # 單位數 − 1

# (control, 說明)。順序即畫面上的列號。
CASES = [
    (0x8800, "byte，兩端遞增"),
    (0x9800, "word，兩端遞增"),
    (0x8C00, "byte，目的遞減"),
    (0x8A00, "byte，來源遞減"),
    (0x9C00, "word，目的遞減"),
    (0x9A00, "word，來源遞減"),
    (0x9900, "word ＋ bit8（每 16 byte 退 16）"),
    (0xA800, "特例值"),
    (0x8000, "只有 bit15"),
    (0x0800, "只有 bit11"),
    (0x8801, "觸發 ＋ 未知低位元"),
    (0x9808, "word ＋ 未知低位元"),
]
FAULT_CASE = (0x0001, "沒有觸發位元的非零值")


def deswap(data: bytes) -> bytes:
    return bytes(data[i ^ 1] for i in range(len(data)))


def make_palette() -> bytes:
    """索引原樣編進顏色：r 帶低 3 位、g 帶中 3 位、b 帶高 2 位，可逐 byte 反查。"""
    out = bytearray()
    for i in range(256):
        r = (i & 7) * 4 + 3
        g = ((i >> 3) & 7) * 4 + 3
        b = (i >> 6) * 8 + 3
        out += struct.pack(">H", (b << 10) | (g << 5) | r)
    return bytes(out)


def make_pattern() -> bytes:
    """64 byte 來源：值 = 索引 + 1，因此 0 只會來自「沒被搬到」以外的原因。"""
    return bytes((i + 1) & 0xff for i in range(64))


def make_map(cases) -> bytes:
    """每個案例佔一列：第 0–3 欄是目的區的四張 tile，第 5 欄是暫存器回讀。"""
    entries = [[0] * 32 for _ in range(32)]
    for index in range(len(cases)):
        for column in range(4):
            entries[index][column] = 1 + index * 4 + column
        entries[index][5] = 49 + index
    out = bytearray()
    for row in entries:
        for value in row:
            out += struct.pack(">H", value)
    return bytes(out)


def make_cases(cases) -> bytes:
    out = bytearray()
    for index, (control, _) in enumerate(cases):
        destination = VRAM_BASE + 64 + 256 * index + 128
        out += struct.pack(">6H", PATTERN_ADDR >> 16, PATTERN_ADDR & 0xffff,
                           destination >> 16, destination & 0xffff, COUNT, control)
    return bytes(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--auth-rom", required=True)
    ap.add_argument("--fault-case", action="store_true",
                    help="追加一個沒有觸發位元的非零 control。反編譯顯示 Bcan 對它回錯誤碼，"
                         "可能導致安全停機，因此預設不含")
    ap.add_argument("--image", default="acan-m68k:bookworm-v1")
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    cases = CASES + ([FAULT_CASE] if args.fault_case else [])
    out_name = args.out or ("dmaprobe-fault.bin" if args.fault_case else "dmaprobe.bin")

    os.makedirs(BUILD, exist_ok=True)
    cart = deswap(open(args.auth_rom, "rb").read())
    auth = cart[AUTH_OFFSET:AUTH_OFFSET + AUTH_SIZE]
    if len(auth) != AUTH_SIZE:
        print("來源 ROM 太小，取不到授權區", file=sys.stderr)
        return 1
    open(os.path.join(BUILD, "auth.bin"), "wb").write(auth)
    open(os.path.join(BUILD, "palette.bin"), "wb").write(make_palette())
    open(os.path.join(BUILD, "pattern.bin"), "wb").write(make_pattern())
    open(os.path.join(BUILD, "map.bin"), "wb").write(make_map(cases))
    open(os.path.join(BUILD, "cases.bin"), "wb").write(make_cases(cases))
    open(os.path.join(BUILD, "count.inc"), "w").write(f"        .word   {len(cases) - 1}\n")

    print(f"{len(cases)} 個案例，每個搬 {COUNT + 1} 個單位")
    print("列 control 說明")
    for index, (control, note) in enumerate(cases):
        print(f"{index:2d} ${control:04X} {note}")

    uid = f"{os.getuid()}:{os.getgid()}"
    cmd = [
        "docker", "run", "--rm", "--network", "none", "--memory", "512m", "--cpus", "1",
        "--pids-limit", "128", "-u", uid, "-v", f"{ROOT}:/src", "-w", "/src",
        "--log-opt", "max-size=10m", "--log-opt", "max-file=3", args.image, "sh", "-c",
        "m68k-linux-gnu-as -m68000 -o build/probe.o probe.s && "
        "m68k-linux-gnu-ld -Ttext=0 -o build/probe.elf build/probe.o && "
        "m68k-linux-gnu-objcopy -O binary build/probe.elf build/probe.img",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.stderr.write(result.stdout + result.stderr)
        return result.returncode

    image = bytearray(open(os.path.join(BUILD, "probe.img"), "rb").read())
    if len(image) > ROM_SIZE:
        print(f"映像 {len(image)} byte 超過 {ROM_SIZE}", file=sys.stderr)
        return 1
    image += b"\xff" * (ROM_SIZE - len(image))
    if bytes(image[AUTH_OFFSET:AUTH_OFFSET + AUTH_SIZE]) != auth:
        print("授權區未落在預期位置", file=sys.stderr)
        return 1
    out = os.path.join(BUILD, out_name)
    open(out, "wb").write(deswap(bytes(image)))
    print(f"輸出 {out} 大小 {len(image)} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
