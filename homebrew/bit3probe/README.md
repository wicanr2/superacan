# bit3probe：`$F001F0` bit 3 的自製測試卡帶

這是一顆自製的 Super A'Can 卡帶映像，用途是製造出商業 ROM 上不會出現的狀態：
**ROZ 層以 8bpp region 運作，同時 `$F001F0` 的 pixel mode 在 `$0001` 與 `$0009`
之間切換**。八款流通 ROM 從來不讓這兩件事同時成立（量測見
[../../docs/f003-video-mode.md](../../docs/f003-video-mode.md) §7.5），因此無法用它們
回答 bit 3 的行為；這顆 ROM 可以，而且同一份映像能在 Bcan、本專案模擬器與（日後）
實機上跑同一段程式。

## 版權邊界

映像的 `$2000–$23FF` 是卡帶授權區，1024 bytes，八款流通 ROM 完全相同；BIOS 的 IPL
會逐 word 比對並再算兩組校驗值，不放它就開不了機。建置時由**使用者自己的 ROM** 取出，
因此產物 `build/*.bin` 含有版權資料：**只留在本機，不進版控、不散布**。
repo 只收原始碼與建置腳本；`.gitignore` 已排除 `*.bin`。

## 建置

```sh
docker build -t acan-m68k:bookworm-v1 - <<'DOCKERFILE'
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
        binutils-m68k-linux-gnu python3 && rm -rf /var/lib/apt/lists/*
DOCKERFILE

python3 build.py --auth-rom "../../Bcan008b/ROMS/Boom Zoo (Taiwan).bin"
```

參數 `--roz-mode`（`$F00180`）與 `--roz-tile-mode`（`$F00182`）可做變體，用來分離
「哪個暫存器位元參與哪個判斷」。輸出為 512 KiB、與流通 dump 相同的 16-bit word-swap 格式。

## ROM 做了什麼

1. 寫入 256 色調色盤：`index i` → `r = i & 31`、`g = (i >> 3) & 31`、`b = 31 - (i & 31)`。
2. 寫入四個 8bpp tile 與 32×32 的 ROZ tilemap。tile 圖樣對水平與垂直翻轉皆對稱，因為
   `$F00180` 的 region 位元同時是 flip 位元，對稱圖樣可避免翻轉差異混進判讀；tilemap
   不使用 tile 0。
3. 把 tile 之後的整片 VRAM 填成索引 200。加上第 2 點，128 KiB 視窗內沒有任何零 byte，
   因此「畫面空白」只可能是整層未繪製，不可能是取到零值。
4. 設定 ROZ：identity 變換（A=D=`$0100`、B=C=0）、scroll 0、map base 在 VRAM word `$1000`。
5. 主迴圈輪詢 `$F00000` bit 15 等幀，每 300 幀把 `$F001F0` 在 `$0001`／`$0009` 之間切換，
   並把 backdrop（調色盤索引 0）設成紅（bit 3 開）或綠（bit 3 關）。單看一張截圖的底色
   就能判斷相位，整層沒畫出來時也不會誤判。索引 255 恆為白，作為地圖中央的標示方塊。

## 結果（2026-09-01）

同一顆映像：

| 執行環境 | bit 3 = 0 | bit 3 = 1 |
|---|---|---|
| Bcan 0.0.8b | tile 圖樣（一般 tilemap 路徑） | 整片索引 200，即 VRAM 填值（線性 bitmap 路徑） |
| `../superacan-emu` | 同上 | 同上（實作 bitmap 路徑後兩相位皆逐像素相同） |

也就是說 bit 3 是 ROZ 層的 **tilemap／bitmap 切換**。bitmap 的 byte 基底以對照實驗定位：
`--roz-tile-bank 0x0800` 把 tilemap 區（高位元組為零、因此透明）造成的橫向條紋從畫面
第 32–39 列移到第 0–7 列，符合 `4 × $F00196` 與 256 byte 的每列跨距。

反編譯側的公式、指令位址與其餘證據見
[../../docs/f003-video-mode.md](../../docs/f003-video-mode.md) §7.3、§7.6。

## Bcan 的執行方式

Bcan 不吃命令列 ROM 參數，必須走 GUI：`檔案(F)` → 第一項 → 在檔名欄輸入
`Z:\work\bcan\ROMS\<檔名>`。截圖熱鍵為 F8（`Bcan.ini` 的 `hotkey_screenshot=119`），
存到 `snap\`。
