# pixelmodeprobe：`$F001F0` pixel mode（bits 4–3）的四相位掃描

`bit3probe` 定案了 bit 3 是 ROZ 的 tilemap／bitmap 切換，但 bit 4 一直沒碰過。
這顆卡帶用同一個場景（ROZ 停在 8bpp region）把 `$F001F0` 在四個值之間循環，
每個相位一種顏色，直接量 bit 4 到底做不做事。

結論寫在 [../../docs/f003-video-mode.md](../../docs/f003-video-mode.md) §7.7。

## 版權邊界

授權區 `$2000–$23FF`（1024 bytes）建置時由**使用者自己的 ROM** 取出，產物 `build/*.bin`
因此含版權資料：只留本機，不進版控。

## 建置

```sh
python3 build.py --auth-rom "../../Bcan008b/ROMS/Boom Zoo (Taiwan).bin" --out pixelmodeprobe.bin
```

## ROM 做了什麼

場景與 `bit3probe` 相同：ROZ 為 8bpp region、identity 變換、整片 VRAM 填成索引 200
且沒有零 byte。差別在主迴圈每 300 幀把 `$F001F0` 換成下一個值，gfx mode 固定 `2`
（layer 0 為 8bpp）：

| 相位 | `$F001F0` | pixel mode |
|---|---|---|
| 0 | `$02` | `$00` |
| 1 | `$0A` | `$08` |
| 2 | `$12` | `$10` |
| 3 | `$1A` | `$18` |

每個相位同時把調色盤索引 0（backdrop）與 255（地圖中央的標示方塊）改成該相位的顏色。
兩個都改是必要的：ROZ 蓋滿整個畫面時 backdrop 看不見，只改索引 0 的話截圖分不出相位。

## 結果（2026-09-02）

| 相位 | ROZ 走哪條路 | 畫面雜湊（前 10 碼）|
|---|---|---|
| `pm=$00` | tilemap | `99548f2e45` |
| `pm=$08` | **bitmap** | `985c1c47fc` |
| `pm=$10` | tilemap | `a46b257b55` |
| `pm=$18` | tilemap | `543f68c4eb` |

Bcan 0.0.8b 產生的四張畫面與本專案 Linux 重製**完全相同**（同一組雜湊）。三個 tilemap
相位的雜湊互不相同，只是因為標示顏色不同。

也就是說 **bit 4 沒有自己的作用；它唯一可觀察的效果是「設起來就讓 bit 3 的 bitmap 路徑
失效」**——因為條件要求 pixel mode 恰為 `$08`，不是「bit 3 有設」。
