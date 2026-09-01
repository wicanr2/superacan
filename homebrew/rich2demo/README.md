# rich2demo：大富翁2 台灣棋盤的 Super A'Can demo

一顆自製的 1 MiB Super A'Can 卡帶：以原版的 11×11 地圖視窗顯示《大富翁2》台灣棋盤，
按 A 擲骰，棋子沿道路網移動，岔路可用方向鍵指定走哪一條、一秒不指定就照原版的做法
隨機挑。畫面在 Bcan 0.0.8b 與本機 Linux 重製上都跑得起來。

## 版權邊界

三種版權輸入都在建置時從**使用者自己的檔案**取得，產物 `build/*.bin` 因此含有版權資料：
**只留在本機，不進版控、不散布**。repo 只收原始碼與建置腳本。

| 輸入 | 來源 | 用途 |
|---|---|---|
| 卡帶授權區 `$2000–$23FF` | 本機任一款 A'Can ROM（八款完全相同的 1024 bytes） | 通過 BIOS 的 IPL 檢查 |
| 棋盤結構、36×36 地圖圖層 | `SAVE_2.DSK` 區段 3／4 | 格座標、鄰接、地形索引 |
| 131 張 24×20 地圖圖磚、256 色調色盤 | `PART1.PAK` 區段 0、`256.PAT` | 畫面 |

## 建置

素材先由 rich2 專案匯出（該專案的 `internal/assets` 已有完整解析器），再交給本目錄：

```sh
# 1) 匯出素材：board.json / layers.json / maptiles.bin / palette.bin
#    以 rich2 模組內的一支小程式呼叫 assets.ParseBoard / ParseMapLayers /
#    DecodeMapTiles / ParsePalette 即可（internal 套件不能從模組外 import）。
# 2) 組出卡帶
python3 build.py --assets <匯出目錄> --auth-rom "../../Bcan008b/ROMS/Boom Zoo (Taiwan).bin"
```

工具鏈是 `acan-m68k:bookworm-v1`（Debian `binutils-m68k-linux-gnu`），與
`../bit3probe/README.md` 同一個映像。

## 畫面怎麼組出來的

A'Can 的 tilemap 是 8×8，原版地圖圖磚是 24×20——高度不是 8 的倍數，沒辦法直接當 tile 用。
所以把 11×11 格攤成 264×220 的畫布，**寫進 VRAM 時就排成 8×8 packed 8bpp 的 tile**
（33×28 ＝ 924 張），tilemap 用線性索引指過去，等於用 tilemap 硬體顯示一張點陣圖。

24 是 8 的倍數，所以來源每一列正好落在三張相鄰 tile 的同一列上，搬移就只是
「三段 8 bytes、目的間隔 64」；每列 6 個 `move.l`，整個視窗約 14,520 個，一次重畫
大約 0.03 秒。棋子直接蓋在畫好的 tile 版面上，不用 sprite。

VRAM 版面：tile 資料 `$00000–$0E6FF`、空白 tile 1023 在 `$0FFC0`、tilemap `$12000`。
`$F001F0` 設 gfx mode 2，layer 0 因此是 8bpp（`docs/f003-video-mode.md` §7.2 的 region 表）。

## 手把要靠 65C02

手把是序列移位介面，`$0407` 的位元由 1 變 0 觸發 latch／移位，結果讀 `$0402`——
這條路只有 65C02 走得到。68k 讀的是 65C02 寫進 sound RAM `$0200` 的結果。
所以這顆 ROM 會先把 41 bytes 的掃描迴圈上傳到 sound RAM `$0500`、設好 reset 向量，
再寫 `$E9001C` bit0 放開 65C02。

這件事有實測差異：**本專案的 Linux 重製在 68k 讀 `$E80200` 時直接合成宿主輸入**，
所以少了驅動也能動；**Bcan 不合成**，沒有 65C02 驅動就完全沒有反應。要判斷輸入路徑
是否真的正確，得以 Bcan 為準。

## 已知落差

- **只畫地形層**。原版底圖畫完還會讀疊加層（`docs/re/042` §1 的 `125Ah[row][col]`）
  補上棋子與物件，那批圖形不在 24×20 圖磚裡。因此有些非街道格看起來是水面或空地。
- **Bcan 與本專案對 sprite 表的解讀不同**。同一筆 `w0=$4000 w1=$4000 w2=x w3=$8000`
  在本專案畫出 8×8 一張圖，在 Bcan 畫成一條約 40×6 的橫條。這顆 ROM 改用 tile 版面
  繪製棋子後兩邊完全一致（初始畫面逐像素相同，相異 0／76800），但 sprite 欄位語意的
  分歧本身還沒查清楚。
- 沒有音效、沒有規則（買地、租金、卡片一概沒有），只有移動。
