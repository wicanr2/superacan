#!/usr/bin/env python3
"""建置 sprite 縮放欄位的測試卡帶。

畫面上排成 4×6 的網格，每個 sprite 只差一個欄位值，量它畫出來的方框大小就能
反推欄位語意。授權區由本機既有 ROM 取出，產物只留本機。
"""
import argparse, os, struct, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, "build")
ROM_SIZE = 0x80000
AUTH_OFFSET, AUTH_SIZE = 0x2000, 0x400

# 每一格是一筆 sprite 表項目。第 1 頁掃縮放與 mosaic，第 2 頁掃翻轉與多 tile。
# 1:1 的組合是 hscale=5、vscale=2；mosaic = word1 bits 5-3 的值 + 1。
# 欄位：(hscale, vscale, mosaicField, xlog, ySizeIndex, flipX, flipY, tileEntry)
NEUTRAL = dict(hscale=5, vscale=2, mos=0, xlog=0, ysize=0, fx=0, fy=0, w3=0x8000 | 1)


def case(**kw):
    c = dict(NEUTRAL)
    c.update(kw)
    return c


PAGE1 = (
    [case(hscale=h, mos=7) for h in (0, 1, 2, 3, 4, 5)]
    + [case(hscale=h, mos=7) for h in (6, 8, 12, 16, 24, 31)]
    + [case(vscale=v, mos=7) for v in (0, 1, 2, 3, 4, 7)]
    + [case(mos=m) for m in (0, 1, 2, 3, 5, 7)]
)

# 子 tile 表：2×2 放在 word index $C00（w3=$600），1×4 放在 $C10（w3=$608）。
SUBTABLE_2X2, SUBTABLE_1X4 = 0x600, 0x608

PAGE2 = (
    # 翻轉：整體 flip 兩軸、以及 tile entry 自帶的 flip 位元
    [case(), case(fx=1), case(fy=1), case(fx=1, fy=1),
     case(w3=0x8000 | 0x0800 | 1), case(w3=0x8000 | 0x0400 | 1)]
    # 翻轉配上縮放，檢查兩者的先後順序
    + [case(hscale=2), case(hscale=2, fx=1), case(hscale=2, fy=1),
       case(hscale=2, fx=1, fy=1), case(hscale=1, fx=1), case(vscale=1, fy=1)]
    # 多 tile：2×2 走子 tile 表
    + [case(xlog=1, ysize=1, w3=SUBTABLE_2X2),
       case(xlog=1, ysize=1, w3=SUBTABLE_2X2, fx=1),
       case(xlog=1, ysize=1, w3=SUBTABLE_2X2, fy=1),
       case(xlog=1, ysize=1, w3=SUBTABLE_2X2, fx=1, fy=1),
       case(xlog=1, ysize=1, w3=SUBTABLE_2X2, mos=1),
       case(xlog=1, ysize=1, w3=SUBTABLE_2X2, hscale=2)]
    # ySize 索引：1／2／3／4 tile 高，走 1×4 子表
    + [case(ysize=n, w3=SUBTABLE_1X4) for n in (0, 1, 2, 3)]
    + [case(ysize=3, w3=SUBTABLE_1X4, fy=1), case(ysize=3, w3=SUBTABLE_1X4, vscale=1)]
)

COLS, ROWS = 6, 4
X0, XSTEP = 8, 52
Y0, YSTEP = 24, 56
TILE = 1                    # sprite 圖形放在 tile 1（VRAM byte 64）


def deswap(data: bytes) -> bytes:
    return bytes(data[i ^ 1] for i in range(len(data)))


def make_palette() -> bytes:
    """索引把來源座標與 tile 編號編進顏色：r 帶 x、g 帶 y、b 帶 tile。

    這樣截圖上每一個 sprite 像素都能反推它取樣自哪一張 tile 的哪一格，
    縮放、mosaic 與翻轉的取樣函式就不必用猜的。
    """
    out = bytearray()
    for i in range(256):
        r = (i & 7) * 4 + 3
        g = ((i >> 3) & 7) * 4 + 3
        b = (i >> 6) * 8 + 3
        out += struct.pack(">H", (b << 10) | (g << 5) | r)
    return bytes(out)


def make_sprites(cases) -> bytes:
    out = bytearray()
    for index, c in enumerate(cases):
        x = X0 + (index % COLS) * XSTEP
        y = Y0 + (index // COLS) * YSTEP
        word0 = (c["vscale"] << 13) | (c["ysize"] << 9) | (y & 0x1ff)
        word1 = (c["fx"] << 11) | (c["fy"] << 10) | (c["mos"] << 3) | c["xlog"]
        word2 = (c["hscale"] << 11) | (0 << 9) | (x & 0x1ff)
        out += struct.pack(">4H", word0, word1, word2, c["w3"])
    return bytes(out)


def make_subtables() -> bytes:
    """VRAM byte $1800 起：2×2 用 tile 1-4，1×4 用 tile 1-4 直向排。"""
    out = bytearray()
    out += struct.pack(">4H", 1, 2, 3, 4)          # $C00：2×2
    out += struct.pack(">4H", 0, 0, 0, 0)          # 補到 $C10
    out += struct.pack(">4H", 1, 2, 3, 4)          # $C10：1×4
    return bytes(out)


def decoder_tiles() -> bytes:
    """四張 8×8 解碼圖：tile t 的像素值 = x + 8y + 64t，配合調色盤可反推 (x, y, t)。"""
    out = bytearray()
    for t in range(4):
        for y in range(8):
            for x in range(8):
                out.append(x + 8 * y + 64 * t)
    return bytes(out)


def predictions(cases) -> list:
    """依 Bcan 反編譯的公式算出預期寬高，供量測比對。"""
    rows_out = []
    for c in cases:
        native_w = 8 if (c["w3"] & 0x8000) else 8 << c["xlog"]
        native_h = 8 if (c["w3"] & 0x8000) else 8 * YSIZE_TABLE[c["ysize"]]
        width = (c["hscale"] + 6 * native_w) // (c["hscale"] + 1)
        height = 3 * native_h if c["vscale"] == 0 else \
            (c["vscale"] + 2 * native_h - 1) // c["vscale"]
        rows_out.append((c, min(width, 256), min(height, 256)))
    return rows_out


YSIZE_TABLE = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 16, 20, 22, 24, 26)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--auth-rom", required=True)
    ap.add_argument("--page", type=int, choices=(1, 2), default=1,
                    help="1：縮放與 mosaic；2：翻轉與多 tile")
    ap.add_argument("--image", default="acan-m68k:bookworm-v1")
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    cases = PAGE1 if args.page == 1 else PAGE2
    out_name = args.out or f"spriteprobe{args.page}.bin"

    os.makedirs(BUILD, exist_ok=True)
    cart = deswap(open(args.auth_rom, "rb").read())
    auth = cart[AUTH_OFFSET:AUTH_OFFSET + AUTH_SIZE]
    if len(auth) != AUTH_SIZE:
        print("來源 ROM 太小，取不到授權區", file=sys.stderr)
        return 1
    open(os.path.join(BUILD, "auth.bin"), "wb").write(auth)
    open(os.path.join(BUILD, "palette.bin"), "wb").write(make_palette())
    open(os.path.join(BUILD, "tile.bin"), "wb").write(decoder_tiles())
    open(os.path.join(BUILD, "subtable.bin"), "wb").write(make_subtables())
    open(os.path.join(BUILD, "sprites.bin"), "wb").write(make_sprites(cases))
    open(os.path.join(BUILD, "count.inc"), "w").write(
        f"        .word   {len(cases) - 1}\n")

    print(f"第 {args.page} 頁，{len(cases)} 個案例")
    print("格號 hs vs mos xlog ys fx fy    w3 | 預期 w×h | 位置")
    for index, (c, w, h) in enumerate(predictions(cases)):
        x = X0 + (index % COLS) * XSTEP
        y = Y0 + (index // COLS) * YSTEP
        print(f"{index:4d} {c['hscale']:2d} {c['vscale']:2d} {c['mos']:3d} "
              f"{c['xlog']:4d} {c['ysize']:2d} {c['fx']:2d} {c['fy']:2d} "
              f"${c['w3']:04X} | {w:3d}×{h:<3d} | ({x},{y})")

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
