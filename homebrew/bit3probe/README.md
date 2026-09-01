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
   `index 0` 因此是純藍，這同時也是未繪製區域（backdrop）的顏色。
2. 寫入四個 8bpp tile 與 32×32 的 ROZ tilemap。tile 圖樣對水平與垂直翻轉皆對稱，
   因為 `$F00180` 的 region 位元同時是 flip 位元，對稱圖樣可避免翻轉差異混進判讀。
3. 設定 ROZ：identity 變換（A=D=`$0100`、B=C=0）、scroll 0、map base 在 VRAM word `$1000`。
4. 主迴圈輪詢 `$F00000` bit 15 等幀，每 180 幀把 `$F001F0` 在 `$0001`／`$0009` 之間切換，
   並把調色盤第 255 號改成紅（bit 3 開）或藍（bit 3 關）作為相位標示。

## 第一輪結果（2026-09-01）

同一顆映像：

| 執行環境 | bit 3 = 0 | bit 3 = 1 |
|---|---|---|
| 本專案 Go renderer | 畫出 ROZ 圖樣 | 畫出 ROZ 圖樣（只有標示方塊變色） |
| Bcan 0.0.8b | **整片 backdrop（palette 0），ROZ 層不出現** | 畫出 ROZ 圖樣 |

也就是說，在同一組暫存器設定下，**Bcan 只有在 bit 3 設起來時才畫出 8bpp 的 ROZ 層**。
這是目前第一個可重現、可觀察的 bit 3 行為差異，來源是自製軟體而非商業 ROM。

尚未定案：確切的閘門條件。`$F00182` bit 8（依反編譯推測為 Bcan 逐行表判斷的一部分）
設為 1 的變體 C 沒有改變結果，代表閘門不只這一項，或該位元的位置判讀有誤。下一輪要做的是
把 palette 0 改成與標示不同的顏色（現在 backdrop 與 bit3=0 的標示同為藍色，靠推理才排除
歧義），並逐一掃 `$F00180`／`$F00182` 的位元組合。
