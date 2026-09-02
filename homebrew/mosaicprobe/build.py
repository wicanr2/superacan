#!/usr/bin/env python3
"""建置 tilemap／ROZ mosaic 欄位的測試卡帶。

畫面鋪滿 16×16 的解碼圖樣，每個螢幕像素都能反推來源座標，因此 mosaic 的塊大小與
塊原點可以直接量出來。授權區由本機既有 ROM 取出，產物只留本機。
"""
import argparse, os, struct, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, "build")
ROM_SIZE = 0x80000
AUTH_OFFSET, AUTH_SIZE = 0x2000, 0x400


def deswap(data: bytes) -> bytes:
    return bytes(data[i ^ 1] for i in range(len(data)))


def make_palette() -> bytes:
    """索引把來源座標編進顏色：r 帶 x&7、g 帶 y&7、b 帶 tile 編號。"""
    out = bytearray()
    for i in range(256):
        r = (i & 7) * 4 + 3
        g = ((i >> 3) & 7) * 4 + 3
        b = (i >> 6) * 8 + 3
        out += struct.pack(">H", (b << 10) | (g << 5) | r)
    return bytes(out)


def decoder_tiles() -> bytes:
    """四張 8×8 解碼圖：tile t 的像素值 = x + 8y + 64t。"""
    out = bytearray()
    for t in range(4):
        for y in range(8):
            for x in range(8):
                out.append(x + 8 * y + 64 * t)
    return bytes(out)


def make_map() -> bytes:
    """32×32 的 tilemap，2×2 輪流使用四張 tile，使來源圖樣以 16 像素為週期。"""
    out = bytearray()
    for row in range(32):
        for col in range(32):
            out += struct.pack(">H", (col & 1) + 2 * (row & 1))
    return bytes(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--auth-rom", required=True)
    ap.add_argument("--mosaic", type=int, choices=range(8), default=0,
                    help="mosaic 欄位值（flags bits 4-2）")
    ap.add_argument("--layer", choices=("tile", "roz"), default="tile")
    ap.add_argument("--image", default="acan-m68k:bookworm-v1")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    # 一般圖層 0：32×32、wrap、mosaic；ROZ：region 3（8bpp）、32×32、wrap、mosaic。
    layer_flags = 0x0420 | (args.mosaic << 2)
    roz_mode = 0x0423 | (args.mosaic << 2)
    video = 0x0100 | (0x0080 if args.layer == "tile" else 0x0004)
    out_name = args.out or f"mosaicprobe-{args.layer}{args.mosaic}.bin"

    os.makedirs(BUILD, exist_ok=True)
    cart = deswap(open(args.auth_rom, "rb").read())
    auth = cart[AUTH_OFFSET:AUTH_OFFSET + AUTH_SIZE]
    if len(auth) != AUTH_SIZE:
        print("來源 ROM 太小，取不到授權區", file=sys.stderr)
        return 1
    open(os.path.join(BUILD, "auth.bin"), "wb").write(auth)
    open(os.path.join(BUILD, "palette.bin"), "wb").write(make_palette())
    open(os.path.join(BUILD, "tile.bin"), "wb").write(decoder_tiles())
    open(os.path.join(BUILD, "map.bin"), "wb").write(make_map())
    open(os.path.join(BUILD, "cfg.inc"), "w").write(
        f"        .word   0x{video:04X}\n"
        f"        .word   0x0002\n"
        f"        .word   0x{layer_flags:04X}\n"
        f"        .word   0x{roz_mode:04X}\n")

    block = args.mosaic + 1
    print(f"層 {args.layer}、mosaic 欄位 {args.mosaic}")
    print(f"  查表模型：塊大小 {block}，來源座標 = floor(d/{block})×{block}")
    print(f"  位元遮罩模型：塊大小 {1 << args.mosaic}，來源座標 = d & ~{(1 << args.mosaic) - 1}")

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
