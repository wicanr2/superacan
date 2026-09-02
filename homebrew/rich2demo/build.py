#!/usr/bin/env python3
"""建置大富翁2 台灣棋盤的 Super A'Can demo 卡帶。

素材（棋盤結構、地圖圖層、24×20 圖磚、調色盤）由 rich2 專案的匯出目錄取得，
授權區由本機既有 A'Can ROM 取出。兩者都是版權輸入：產物只留本機，不進版控。
"""
import argparse, hashlib, json, os, struct, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, "build")
MANIFEST = os.path.join(ROOT, "manifest.json")
ROM_SIZE = 0x100000            # 1 MiB
AUTH_OFFSET, AUTH_SIZE = 0x2000, 0x400
SQUARE_SLOTS = 119             # 台灣的槽位上限
TILE_COUNT = 131               # PART1.PAK 區段 0 的圖磚張數
MAP_SIZE = 36
TILE_W, TILE_H = 24, 20


def sha256(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def collect_hashes(args, out_path: str) -> dict:
    """記錄整條重現鏈的雜湊：原版輸入 → 匯出素材 → 中間產物 → 卡帶映像。

    版權檔案本身不進版控，但雜湊可以——有了它，任何人拿自己的合法原版都能確認
    重跑出來的是位元相同的東西。
    """
    entry = {"inputs": {}, "exported": {}, "generated": {}, "rom": {}}
    if args.orig:
        for name in ("PART1.PAK", "256.PAT", os.path.basename(args.save)):
            path = os.path.join(args.orig, name)
            if os.path.exists(path):
                entry["inputs"][name] = sha256(path)
    entry["inputs"][os.path.basename(args.auth_rom)] = sha256(args.auth_rom)
    for name in ("board.json", "layers.json", "maptiles.bin", "palette.bin"):
        path = os.path.join(args.assets, name)
        if os.path.exists(path):
            entry["exported"][name] = sha256(path)
    for name in ("auth.bin", "palette.bin", "terrain.bin", "squares.bin",
                 "maptiles.bin", "token.bin", "sounddrv.bin"):
        path = os.path.join(BUILD, name)
        if os.path.exists(path):
            entry["generated"][name] = sha256(path)
    entry["rom"] = {"name": os.path.basename(out_path),
                    "size": os.path.getsize(out_path), "sha256": sha256(out_path)}
    return entry


def check_manifest(art: str, entry: dict, write: bool) -> int:
    data = {}
    if os.path.exists(MANIFEST):
        data = json.load(open(MANIFEST, encoding="utf-8"))
    if write:
        data.setdefault("說明", "rich2demo 重現鏈的雜湊。版權檔案不進版控，雜湊可以。")
        data[art] = entry
        json.dump(data, open(MANIFEST, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2, sort_keys=True)
        print(f"已寫入 manifest.json（{art}）")
        return 0
    recorded = data.get(art)
    if not recorded:
        print(f"manifest.json 沒有 {art} 的紀錄，略過核對")
        return 0
    bad = []
    for section in ("inputs", "exported", "generated"):
        for name, want in recorded.get(section, {}).items():
            got = entry.get(section, {}).get(name)
            if got is None:
                bad.append(f"{section}/{name}：這次沒有產生")
            elif got != want:
                bad.append(f"{section}/{name}：{got[:16]} ≠ 記錄的 {want[:16]}")
    if recorded["rom"]["sha256"] != entry["rom"]["sha256"]:
        bad.append(f"rom：{entry['rom']['sha256'][:16]} ≠ 記錄的 "
                   f"{recorded['rom']['sha256'][:16]}")
    if bad:
        print("與 manifest.json 不符：", file=sys.stderr)
        for line in bad:
            print("  " + line, file=sys.stderr)
        return 1
    print(f"與 manifest.json 相符（{art}）")
    return 0


def deswap(data: bytes) -> bytes:
    return bytes(data[i ^ 1] for i in range(len(data)))


def to_xbgr555(rgb: bytes) -> bytes:
    out = bytearray()
    for i in range(256):
        r, g, b = rgb[i * 3] >> 3, rgb[i * 3 + 1] >> 3, rgb[i * 3 + 2] >> 3
        out += struct.pack(">H", (b << 10) | (g << 5) | r)
    return bytes(out)


def brightest(rgb: bytes) -> int:
    """挑一個夠亮的調色盤索引當棋子顏色；索引 0 是透明色，排除。"""
    best, score = 1, -1
    for i in range(1, 256):
        r, g, b = rgb[i * 3:i * 3 + 3]
        value = min(r, g, b) * 3 + r + g + b
        if value > score:
            best, score = i, value
    return best


def placeholder_palette() -> bytes:
    """佔位模式的調色盤：0 底色、8 格線、15 棋子，16 起是 131 種可區分的地形色。

    這組顏色與原版無關，是為了讓截圖可以進版控而自己配的。
    """
    out = bytearray(512)

    def put(index, r, g, b):
        struct.pack_into(">H", out, index * 2, (b << 10) | (g << 5) | r)

    put(0, 3, 3, 5)
    put(8, 9, 9, 11)
    put(15, 31, 31, 31)
    for i in range(TILE_COUNT):
        # 沿色相環走，明度三段交錯讓相鄰索引不撞色；再往中灰混一半壓低彩度，
        # 否則整張圖會變成看不出結構的彩色雜訊。
        hue = (i * 37) % 96 / 96.0
        level = 20 + (i % 3) * 5
        sector, frac = int(hue * 6) % 6, hue * 6 % 1.0
        high, low, mid = level, level // 3, int(level * (0.35 + 0.55 * frac))
        rgb = [(high, mid, low), (mid, high, low), (low, high, mid),
               (low, mid, high), (mid, low, high), (high, low, mid)][sector]
        grey = sum(rgb) // 3
        put(16 + i, *[(c + grey) // 2 for c in rgb])
    return bytes(out)


def placeholder_tiles() -> bytes:
    """佔位模式的 131 張 24×20 圖塊：每個索引一種顏色，外加一圈格線。

    地形的分佈仍然是原版棋盤的版面，但畫出來的每一個像素都是這裡生成的。
    """
    out = bytearray()
    for i in range(TILE_COUNT):
        for y in range(TILE_H):
            for x in range(TILE_W):
                edge = x == 0 or y == 0 or x == TILE_W - 1 or y == TILE_H - 1
                out.append(8 if edge else 16 + i)
    return bytes(out)


def token_tile(pen: int, edge: int) -> bytes:
    """8×8 的棋子：圓形實心，外圈一圈深色描邊，其餘透明（索引 0）。"""
    out = bytearray()
    for y in range(8):
        for x in range(8):
            d = (x - 3.5) ** 2 + (y - 3.5) ** 2
            out.append(pen if d <= 6.0 else edge if d <= 12.0 else 0)
    return bytes(out)


def sound_driver() -> bytes:
    """65C02 端的手把掃描迴圈。

    手把是序列移位介面：`$0407` 的位元由 1 變 0 觸發動作（bit0 latch、bit2 移一位），
    移位結果讀 `$0402`。硬體上這件事只有 65C02 做得到，68k 讀的是 65C02 寫進
    sound RAM `$0200` 的結果（memory-map.md §7、sound-driver.md §2）。
    值是 active low，這裡先取反再存，讓 68k 端「1 = 按下」。
    """
    return bytes([
        0xA9, 0xFF, 0x8D, 0x07, 0x04,        # LDA #$FF / STA $0407
        0xA9, 0xFE, 0x8D, 0x07, 0x04,        # LDA #$FE / STA $0407  latch
        0xA9, 0xFF, 0x8D, 0x07, 0x04,        # LDA #$FF / STA $0407
        0xA2, 0x08,                          # LDX #8
        0xA9, 0xFB, 0x8D, 0x07, 0x04,        # LDA #$FB / STA $0407  shift
        0xA9, 0xFF, 0x8D, 0x07, 0x04,        # LDA #$FF / STA $0407
        0xCA, 0xD0, 0xF3,                    # DEX / BNE shift
        0xAD, 0x02, 0x04,                    # LDA $0402
        0x49, 0xFF,                          # EOR #$FF
        0x8D, 0x00, 0x02,                    # STA $0200
        0x4C, 0x00, 0x05,                    # JMP $0500
    ])


def pack_squares(board: dict) -> bytes:
    """每格 6 個 word：地圖欄（螢幕 X）、地圖列（螢幕 Y）、四個方向的鄰接格號。

    rich2 的呈現層以棋盤 Col 當地圖列、Row 當地圖欄（其 docs/re/042 §3），
    這裡沿用同一個約定。
    """
    table = bytearray(SQUARE_SLOTS * 12)
    for s in board["squares"]:
        n = s["N"]
        if not 1 <= n <= SQUARE_SLOTS:
            continue
        off = (n - 1) * 12
        struct.pack_into(">6h", table, off, s["Row"], s["Col"], *s["Link"])
    return bytes(table)


def pick_start(board: dict) -> int:
    """起始格取「格號 ≤ 50 的非街道格中，出口數最多的那一格」。

    原版的起始格判定牽涉疊加層座標（rich2 docs/spec/013 §1），demo 不需要
    忠實重現，只要落在道路網上、四通八達即可。
    """
    best, score = 0, -1
    for s in board["squares"]:
        if s["N"] > 50 or s["Land"] != 0 and s["Land"] is not None:
            pass
        if s["N"] > 50:
            continue
        exits = sum(1 for v in s["Link"] if v)
        if exits > score:
            best, score = s["N"], exits
    return best


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--assets", required=True, help="rich2 匯出目錄（board.json 等）")
    ap.add_argument("--auth-rom", required=True, help="本機任一款 A'Can ROM，用來取授權區")
    ap.add_argument("--image", default="acan-m68k:bookworm-v1")
    ap.add_argument("--art", choices=("original", "placeholder"), default="original",
                    help="original：用原版圖磚與調色盤（產物含版權資料，只留本機）；"
                         "placeholder：改用自製佔位圖塊，畫面像素全部由本腳本生成")
    ap.add_argument("--orig", default="",
                    help="原版 RICH2 目錄；給了才會記錄／核對 PART1.PAK 等輸入檔雜湊")
    ap.add_argument("--save", default="SAVE_2.DSK", help="城市存檔檔名，只用於雜湊紀錄")
    ap.add_argument("--write-manifest", action="store_true",
                    help="改寫 manifest.json，而不是拿它核對")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    os.makedirs(BUILD, exist_ok=True)
    board = json.load(open(os.path.join(args.assets, "board.json")))
    layers = json.load(open(os.path.join(args.assets, "layers.json")))
    tiles = open(os.path.join(args.assets, "maptiles.bin"), "rb").read()
    rgb = open(os.path.join(args.assets, "palette.bin"), "rb").read()

    terrain = bytearray()
    for row in layers["terrain"]:
        for value in row:
            if not 0 <= value < len(tiles) // (TILE_W * TILE_H):
                print(f"圖磚索引 {value} 超出範圍", file=sys.stderr)
                return 1
            terrain.append(value)
    if len(terrain) != MAP_SIZE * MAP_SIZE:
        print(f"地圖圖層應為 {MAP_SIZE*MAP_SIZE} 格，實際 {len(terrain)}", file=sys.stderr)
        return 1

    if args.art == "placeholder":
        palette, art, pen, edge = placeholder_palette(), placeholder_tiles(), 15, 8
    else:
        palette, art, pen, edge = to_xbgr555(rgb), tiles, brightest(rgb), 1
    open(os.path.join(BUILD, "palette.bin"), "wb").write(palette)
    open(os.path.join(BUILD, "terrain.bin"), "wb").write(bytes(terrain))
    open(os.path.join(BUILD, "squares.bin"), "wb").write(pack_squares(board))
    open(os.path.join(BUILD, "maptiles.bin"), "wb").write(art)
    open(os.path.join(BUILD, "token.bin"), "wb").write(token_tile(pen, edge))
    open(os.path.join(BUILD, "sounddrv.bin"), "wb").write(sound_driver())
    start = pick_start(board)
    open(os.path.join(BUILD, "start.inc"), "w").write(
        f"        .word   {start}\n")
    print(f"起始格 {start}；美術 {args.art}；棋子索引 {pen}；"
          f"圖磚 {len(art)//(TILE_W*TILE_H)} 張")

    cart = deswap(open(args.auth_rom, "rb").read())
    auth = cart[AUTH_OFFSET:AUTH_OFFSET + AUTH_SIZE]
    if len(auth) != AUTH_SIZE:
        print("來源 ROM 太小，取不到授權區", file=sys.stderr)
        return 1
    open(os.path.join(BUILD, "auth.bin"), "wb").write(auth)

    uid = f"{os.getuid()}:{os.getgid()}"
    cmd = [
        "docker", "run", "--rm", "--network", "none", "--memory", "512m", "--cpus", "1",
        "--pids-limit", "128", "-u", uid, "-v", f"{ROOT}:/src", "-w", "/src",
        "--log-opt", "max-size=10m", "--log-opt", "max-file=3", args.image, "sh", "-c",
        "m68k-linux-gnu-as -m68000 -o build/demo.o demo.s && "
        "m68k-linux-gnu-ld -Ttext=0 -o build/demo.elf build/demo.o && "
        "m68k-linux-gnu-objcopy -O binary build/demo.elf build/demo.img",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.stderr.write(result.stdout + result.stderr)
        return result.returncode

    image = bytearray(open(os.path.join(BUILD, "demo.img"), "rb").read())
    if len(image) > ROM_SIZE:
        print(f"映像 {len(image)} byte 超過 {ROM_SIZE}", file=sys.stderr)
        return 1
    image += b"\xff" * (ROM_SIZE - len(image))
    if bytes(image[AUTH_OFFSET:AUTH_OFFSET + AUTH_SIZE]) != auth:
        print("授權區未落在預期位置", file=sys.stderr)
        return 1
    out = os.path.join(BUILD, args.out or (
        "rich2demo.bin" if args.art == "original" else "rich2demo-placeholder.bin"))
    open(out, "wb").write(deswap(bytes(image)))
    ssp, pc = struct.unpack(">II", bytes(image[:8]))
    print(f"輸出 {out} 大小 {len(image)} bytes；SSP=${ssp:08X} PC=${pc:08X}")
    return check_manifest(args.art, collect_hashes(args, out), args.write_manifest)


if __name__ == "__main__":
    raise SystemExit(main())
