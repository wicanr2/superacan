#!/usr/bin/env python3
"""產生逐遊戲的可重播驗證矩陣。

對每一個本地映像跑兩趟：一趟收指標與畫面檢查點，一趟看它實際碰了哪些硬體功能。
輸出是 markdown 表，結果進 docs/verify-matrix.md；量測本身不含任何 ROM 內容，
只有雜湊與布林值。

用法（模擬器與 BIOS 都是本機研究輸入，路徑由呼叫端給）：

    python3 tools/verify_matrix.py --emu ../superacan-emu/acan-headless \\
        --bios <bios 目錄> --roms Bcan008b/ROMS --frames 1800 > docs/verify-matrix.md
"""
import argparse, hashlib, os, re, subprocess, sys, tempfile

# 功能使用一律從 video flags（$F00008）的致能位元判定，不從功能暫存器的寫入判定。
# 寫入不等於啟用——實測 F005／F003 會把第四層的整個區塊清成 0，四款會寫 window 1 的
# 暫存器，但兩者的致能位元從來沒被設起來。而且 --watch 只保留前 64 筆事件，同時盯多個
# 區段會被最吵的那個淹掉，得到「看起來沒用到」的假陰性。$F00008 的寫入很稀疏，沒這問題。
ENABLE_BITS = [
    (0x80, "normal layer 0"), (0x40, "normal layer 1"), (0x20, "normal layer 2"),
    (0x10, "normal layer 3"), (0x08, "sprite"), (0x04, "ROZ"),
    (0x02, "window 0"), (0x01, "window 1"),
]
METRICS = ("steps", "sound_steps", "framebuffer_nonblack", "vram_nonzero",
           "audio_nonzero", "video_flags", "overlays", "irq_ack", "dma_triggers")


def run(emu, bios, rom, frames, extra):
    cmd = [emu,
           "--ipl", os.path.join(bios, "internal_68k.bin"),
           "--key", os.path.join(bios, "umc6650.bin"),
           "--sound-bios1", os.path.join(bios, "internal_6502_1.bin"),
           "--sound-bios2", os.path.join(bios, "internal_6502_2.bin"),
           "--rom", rom, "--frames", str(frames)] + extra
    return subprocess.run(cmd, capture_output=True, text=True).stdout


def metrics_of(text):
    found = {}
    for token in text.split():
        key, _, value = token.partition("=")
        if key in METRICS:
            found[key] = value
    return found


def checkpoints(directory):
    out = []
    for name in sorted(os.listdir(directory)):
        with open(os.path.join(directory, name), "rb") as f:
            out.append(hashlib.sha256(f.read()).hexdigest()[:8])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emu", required=True)
    ap.add_argument("--bios", required=True)
    ap.add_argument("--roms", required=True)
    ap.add_argument("--frames", type=int, default=1800)
    ap.add_argument("--every", type=int, default=300)
    args = ap.parse_args()

    images = sorted(f for f in os.listdir(args.roms) if f.endswith((".bin", ".zip")))
    rows = []
    for name in images:
        rom = os.path.join(args.roms, name)
        with tempfile.TemporaryDirectory() as shots:
            text = run(args.emu, args.bios, rom, args.frames,
                       ["--screenshot-dir", shots, "--screenshot-every", str(args.every)])
            marks = checkpoints(shots)
        watch = run(args.emu, args.bios, rom, args.frames, ["--watch", "f00008"])
        seen = 0
        for value in re.findall(r"F00008=\$([0-9A-F]{4})", watch):
            seen |= int(value, 16)
        used = [label for bit, label in ENABLE_BITS if seen & bit]
        rows.append((name, metrics_of(text), marks, used))

    print("| 映像 | steps | 非黑像素 | 音訊非零 | 曾致能的圖層 | 畫面檢查點 |")
    print("|---|---:|---:|---:|---|---|")
    for name, m, marks, used in rows:
        print(f"| `{name}` | {m.get('steps','?')} | {m.get('framebuffer_nonblack','?')} "
              f"| {m.get('audio_nonzero','?')} | {'、'.join(used) or '—'} "
              f"| {' '.join(marks)} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
