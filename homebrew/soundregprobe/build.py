#!/usr/bin/env python3
"""建置 UM6619 暫存器列舉卡帶。

65C02 依序對暫存器 $00–$FF 各寫一次，每寫完一個就把「下一個編號」存回 sound RAM
$0600；68k 每幀把它讀出來編進調色盤。因此就算模擬器在某個未知暫存器停住，
截圖的顏色也能反推它停在哪一個。授權區由本機既有 ROM 取出，產物只留本機。
"""
import argparse, os, struct, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, "build")
ROM_SIZE = 0x80000
AUTH_OFFSET, AUTH_SIZE = 0x2000, 0x400


def deswap(data: bytes) -> bytes:
    return bytes(data[i ^ 1] for i in range(len(data)))


def sound_driver(data_byte: int, last_reg: int, skip_reg: int) -> bytes:
    """65C02 端：對 $00–last_reg 每個暫存器寫一次 data_byte 再讀回，存進 $0700+n。

    `$0420` 是位址埠兼狀態（bit0 = busy），寫入編號後插 NOP 延遲；`$0422` 是資料埠。
    讀回前要重新指定一次編號。`skip_reg` 會被跳過——預設是 `$17`（key on/off），
    對參數還是垃圾的通道 key on 會讓 Bcan 的邊界保護整台停住，掃不完後面的暫存器。
    """
    return bytes([
        0xA2, 0x00,                    # 0500 LDX #$00
        0x8E, 0x00, 0x06,              # 0502 L1 STX $0600
        0xE0, skip_reg & 0xFF,         # 0505 CPX #skip
        0xF0, 0x29,                    # 0507 BEQ SKIP
        0xAD, 0x20, 0x04,              # 0509 W1 LDA $0420
        0x4A,                          # 050C LSR A
        0xB0, 0xFA,                    # 050D BCS W1
        0x8E, 0x20, 0x04,              # 050F STX $0420
        0xEA, 0xEA, 0xEA, 0xEA, 0xEA, 0xEA,  # 0512
        0xA9, data_byte & 0xFF,        # 0518 LDA #data
        0x8D, 0x22, 0x04,              # 051A STA $0422
        0xAD, 0x20, 0x04,              # 051D W2 LDA $0420
        0x4A,                          # 0520 LSR A
        0xB0, 0xFA,                    # 0521 BCS W2
        0x8E, 0x20, 0x04,              # 0523 STX $0420   重新指定編號以便讀回
        0xEA, 0xEA, 0xEA, 0xEA, 0xEA, 0xEA,  # 0526
        0xAD, 0x22, 0x04,              # 052C LDA $0422
        0x9D, 0x00, 0x07,              # 052F STA $0700,X
        0xE8,                          # 0532 SKIP INX
        0xE0, (last_reg + 1) & 0xFF,   # 0533 CPX #last+1
        0xD0, 0xCB,                    # 0535 BNE L1
        0xA9, 0x01,                    # 0537 LDA #$01
        0x8D, 0x01, 0x06,              # 0539 STA $0601
        0x4C, 0x3C, 0x05,              # 053C JMP *
    ])


def make_palette() -> bytes:
    """索引 n 的顏色編回 n 本身：r 帶低 3 位、g 帶中 3 位、b 帶高 2 位。

    畫面把 256 個回讀值排成 16×16 色格，每格填滿對應索引，因此截圖能直接反推
    每一個暫存器讀回什麼。
    """
    out = bytearray()
    for i in range(256):
        r = (i & 7) * 4 + 2
        g = ((i >> 3) & 7) * 4 + 2
        b = ((i >> 6) & 3) * 8 + 3
        out += struct.pack(">H", (b << 10) | (g << 5) | r)
    return bytes(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--auth-rom", required=True)
    ap.add_argument("--data", default="0x5A", help="寫進每個暫存器的資料位元組")
    ap.add_argument("--image", default="acan-m68k:bookworm-v1")
    ap.add_argument("--last-reg", default="0xFF", help="只掃到這個暫存器編號")
    ap.add_argument("--skip", default="0x17", help="跳過的暫存器（預設 key on/off）")
    ap.add_argument("--release", default="1", help="1 放開 65C02，0 讓它保持重置")
    ap.add_argument("--out", default="soundregprobe.bin")
    args = ap.parse_args()

    os.makedirs(BUILD, exist_ok=True)
    cart = deswap(open(args.auth_rom, "rb").read())
    auth = cart[AUTH_OFFSET:AUTH_OFFSET + AUTH_SIZE]
    if len(auth) != AUTH_SIZE:
        print("來源 ROM 太小，取不到授權區", file=sys.stderr)
        return 1
    driver = sound_driver(int(args.data, 0), int(args.last_reg, 0), int(args.skip, 0))
    open(os.path.join(BUILD, "auth.bin"), "wb").write(auth)
    open(os.path.join(BUILD, "palette.bin"), "wb").write(make_palette())
    open(os.path.join(BUILD, "sounddrv.bin"), "wb").write(driver)
    open(os.path.join(BUILD, "drvlen.inc"), "w").write(f"        .word   {len(driver) - 1}\n")
    open(os.path.join(BUILD, "release.inc"), "w").write(
        f"        .word   {int(args.release, 0)}\n")

    uid = f"{os.getuid()}:{os.getgid()}"
    cmd = ["docker", "run", "--rm", "--network", "none", "--memory", "512m", "--cpus", "1",
           "--pids-limit", "128", "-u", uid, "-v", f"{ROOT}:/src", "-w", "/src",
           "--log-opt", "max-size=10m", "--log-opt", "max-file=3", args.image, "sh", "-c",
           "m68k-linux-gnu-as -m68000 -o build/probe.o probe.s && "
           "m68k-linux-gnu-ld -Ttext=0 -o build/probe.elf build/probe.o && "
           "m68k-linux-gnu-objcopy -O binary build/probe.elf build/probe.img"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.stderr.write(result.stdout + result.stderr)
        return result.returncode

    image = bytearray(open(os.path.join(BUILD, "probe.img"), "rb").read())
    image += b"\xff" * (ROM_SIZE - len(image))
    if bytes(image[AUTH_OFFSET:AUTH_OFFSET + AUTH_SIZE]) != auth:
        print("授權區未落在預期位置", file=sys.stderr)
        return 1
    out = os.path.join(BUILD, args.out)
    open(out, "wb").write(deswap(bytes(image)))
    print(f"輸出 {out}；驅動 {len(driver)} bytes，掃到 ${int(args.last_reg, 0):02X}，放開 65C02={args.release}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
