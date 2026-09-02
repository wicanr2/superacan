#!/usr/bin/env python3
"""建置 pixelmodeprobe 卡帶映像。

產出 build/pixelmodeprobe.bin，格式與流通 dump 相同（16-bit word-swap）。
授權區 1024 byte 由本機既有 ROM 取出，屬版權輸入：產物只留在本機，
不得進版控或散布。
"""
import argparse, os, struct, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, "build")
ROM_SIZE = 0x80000          # 512 KiB
AUTH_OFFSET, AUTH_SIZE = 0x2000, 0x400


def deswap(data: bytes) -> bytes:
    return bytes(data[i ^ 1] for i in range(len(data)))


def make_palette() -> bytes:
    out = bytearray()
    for i in range(256):
        r = i & 0x1F
        g = (i >> 3) & 0x1F
        b = 31 - (i & 0x1F)
        out += struct.pack(">H", (b << 10) | (g << 5) | r)
    return bytes(out)


def make_tiles() -> bytes:
    """四個 8bpp tile，圖樣對水平與垂直翻轉皆對稱，避免 flip 差異混入判讀。"""
    out = bytearray()
    for tile in range(4):
        for y in range(8):
            for x in range(8):
                if tile == 0:
                    ring = max(abs(x - 3.5), abs(y - 3.5))
                    value = 1 + int(ring) * 40
                elif tile == 1:
                    value = 1 + min(y, 7 - y) * 50
                elif tile == 2:
                    value = 255
                else:
                    value = 1 + ((x & 1) ^ (y & 1)) * 128
                out.append(min(value, 255))
    return bytes(out)


def make_map() -> bytes:
    out = bytearray()
    for ty in range(32):
        for tx in range(32):
            if 15 <= tx <= 16 and 15 <= ty <= 16:
                # 索引 255 的模式標示方塊。放在地圖中央，因為 region 3 同時
                # 是 X/Y flip 位元，角落會被翻到可視區外。
                tile = 2
            elif (tx // 4 + ty // 4) % 2 == 0:
                tile = 1
            elif (tx + ty) % 2 == 0:
                tile = 3
            else:
                tile = 1
            # 不使用 tile 0：map 內容因此不含 0 word，配合 VRAM 填值讓整個
            # 視窗沒有零 byte。
            out += struct.pack(">H", tile)
    return bytes(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--auth-rom", required=True, help="本機任一款流通 ROM，用來取授權區")
    ap.add_argument("--image", default="acan-m68k:bookworm-v1")
    ap.add_argument("--roz-mode", default="0x0423",
                    help="$F00180 的值。0x0423 = 32x32、wrap、8bpp；0x0623 另設 bit 9（逐行表關）")
    ap.add_argument("--roz-tile-mode", default="0x0000",
                    help="$F00182 的值。Bcan 以其 bit 8 作為 ROZ 逐行表的關閉條件之一")
    ap.add_argument("--roz-tile-bank", default="0x0000",
                    help="$F00196 的值；bitmap 模式的基底為其 4 倍")
    ap.add_argument("--out", default="pixelmodeprobe.bin")
    args = ap.parse_args()

    os.makedirs(BUILD, exist_ok=True)
    cart = deswap(open(args.auth_rom, "rb").read())
    auth = cart[AUTH_OFFSET:AUTH_OFFSET + AUTH_SIZE]
    if len(auth) != AUTH_SIZE:
        print("來源 ROM 太小，取不到授權區", file=sys.stderr)
        return 1
    open(os.path.join(BUILD, "auth.bin"), "wb").write(auth)
    open(os.path.join(BUILD, "palette.bin"), "wb").write(make_palette())
    open(os.path.join(BUILD, "tiles.bin"), "wb").write(make_tiles())
    open(os.path.join(BUILD, "rozmap.bin"), "wb").write(make_map())
    # 四個相位掃 $F001F0 的 pixel mode（bits 4-3），gfx mode 固定 2（layer 0 為 8bpp）。
    # 每個相位一種 backdrop 顏色，單看截圖就能判斷當下是哪一個。
    open(os.path.join(BUILD, "phases.inc"), "w").write("".join(
        f"        .word   0x{(pm << 3) | 2:04X}, 0x{colour:04X}\n"
        for pm, colour in ((0, 0x03E0), (1, 0x001F), (2, 0x7C00), (3, 0x7FFF))))
    open(os.path.join(BUILD, "rozmode.inc"), "w").write(
        f"        .word   {int(args.roz_mode, 0)}\n"
        f"        .word   {int(args.roz_tile_mode, 0)}\n"
        f"        .word   {int(args.roz_tile_bank, 0)}\n")

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
    out = os.path.join(BUILD, args.out)
    open(out, "wb").write(deswap(bytes(image)))

    ssp, pc = struct.unpack(">II", bytes(image[:8]))
    print(f"輸出 {out} 大小 {len(image)} bytes；SSP=${ssp:08X} PC=${pc:08X}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
