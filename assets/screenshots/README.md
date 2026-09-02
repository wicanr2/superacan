# 測試截圖的來源與邊界

本目錄只收**畫面內容完全由本庫自製卡帶生成**的截圖：調色盤、圖磚、sprite 圖形都由
對應的 `build.py` 產生，不含任何原版遊戲美術。判讀方式見
[docs/test-screenshots.md](../../docs/test-screenshots.md)。

| 檔案 | 來源 | 像素 SHA-256（前 16 碼）|
|---|---|---|
| `bit3probe-tilemap.png` | Bcan 0.0.8b F8 截圖，`homebrew/bit3probe/`，`$F001F0` bit 3 = 0 | `543f68c4ebe570a2` |
| `bit3probe-bitmap.png` | 同上，bit 3 = 1 | `eae40c77c0b6e8b0` |
| `spriteprobe-page1.png` | Bcan 0.0.8b F8 截圖，`homebrew/spriteprobe/ --page 1` | `c9eedb998bd9ed72` |
| `spriteprobe-page2.png` | 同上，`--page 2` | `f0747610ec2e7f53` |
| `spriteprobe-page3.png` | 同上，`--page 3`（mask 模式 16 種組合）| `ee1900297e9a38c2` |
| `spriteprobe-page4.png` | 同上，`--page 4`（mask=1 的半透明分支）| `a68c0a4edb9ac3c1` |
| `mosaicprobe-tile5.png` | 同上，`homebrew/mosaicprobe/ --layer tile --mosaic 5` | `9137f451e4123775` |
| `dmaprobe.png` | 同上，`homebrew/dmaprobe/`，12 個 control 值 | `9b13c27b58547b88` |
| `rich2demo-initial.png` | 本專案重製跑 `homebrew/rich2demo/ --art placeholder`，第 100 幀 | `b36f497354c69157` |
| `rich2demo-moved.png` | 同上，擲兩次骰之後的第 400 幀 | `2c9c4c2796df3db8` |
| `rich2demo-layout.svg` | 自繪示意圖 | — |

七張探針 PNG 的像素內容與本專案 Linux 重製的輸出逐像素相同；檔案位元組不同是兩邊 PNG
編碼器的差異，不是畫面差異。`dmaprobe.png` 是例外：搬移結果相同，但畫面右側那一欄的
DMA 暫存器回讀 Bcan 一律是 0、本專案是實際值（見 [docs/host-dma.md](../../docs/host-dma.md) §5）。

`rich2demo-initial.png` 的畫面與 Bcan 0.0.8b 跑同一顆映像逐像素相同（相異 0／76,800）。

**不收**：`homebrew/rich2demo/ --art original` 的任何截圖。那個模式畫的是《大富翁2》的
原版地圖圖磚與調色盤，屬受版權保護的美術，只能留在本機。這裡收的兩張是
`--art placeholder`：棋盤版面仍然是原版的道路網，但**每一個像素的顏色都由 `build.py`
生成**，131 種地形各配一色加一圈格線，不含任何原版美術。
