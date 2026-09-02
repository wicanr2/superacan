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
| `rich2demo-layout.svg` | 自繪示意圖 | — |

四張 PNG 的像素內容與本專案 Linux 重製的輸出逐像素相同；檔案位元組不同是兩邊 PNG
編碼器的差異，不是畫面差異。

**不收**：`homebrew/rich2demo/` 的任何截圖。那些畫面是《大富翁2》的原版地圖圖磚與調色盤，
屬受版權保護的美術，只能留在本機。示意圖 `rich2demo-layout.svg` 是自繪的版面說明，
不含原版像素。
