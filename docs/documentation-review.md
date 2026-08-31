# 文件完整度複查與可補來源

更新日期：2026-08-31。此表以「能否支持軟體模擬」為準，不以頁數或未命名 register 數量評分。

| 文件領域 | 現況 | 本輪找到的補強來源 | 下一個有效動作 |
|---|---|---|---|
| BIOS／IPL | 完整涵蓋固定 dump、vectors、控制流與 hash | MAME ROM definitions | 只剩 invalid-key 動態實驗與其他 revision provenance |
| 正式軟體目錄 | 本輪補齊 F001–F012、標題、serial、hash、NVRAM 提示 | MAME `hash/supracan.xml`（CC0） | 對本地九款建立正常玩家路徑矩陣 |
| UM6618 | 位址骨架完整；第四層、pixel/gfx mode、window／IRQ 定義本輪補強 | MAME driver 作者 `hw_docs/pergame.md` `1b9e8fe` | 以 F003/F005/F007 的 consumer 驗證第四層、priority、ROZ／window |
| UM6619 | 主要 PCM／DMA／timer 可實作 | MAME sound device＋本地遊戲 driver | envelope／release 仍需實機或更多 driver consumer |
| UM70C188 | 型號與數位接線已知；找到 UM70C171 原廠資料表；F003 寫 `$F001F0=$0009` 啟用 bit 3 | Bitsavers UMC datasheet＋`PPU.sch`＋本地 ROM | trace F003 `$74C86` 畫面與 pixel bus，確認特殊 mode 是否走 direct-color |
| 卡帶／SRAM | raw ROM、雙 part、32 KiB fallback 已知 | MAME software list＋板級 schematic | 實拍各型卡帶 PCB，確認哪些 serial 真有 SRAM／電池 |
| 主機板 | 16000-2A schematic 已證實 UM6618 `VRAM_A17` 接 SRAM `A16` | `superacan-notes` `PPU.sch` | 以 ROM consumer／logic capture 找出誰產生最高位；不再把配線列為未知 |
| 類比輸出 | 元件與近似邊界已知 | UM70C171、KA2195D datasheet | 要精確只能量測 UM70C188／實機 composite capture |
| 歷史／發售資料 | 基本年份與發行商可由 catalog 固定 | MAME software list | 當年新聞／廣告仍需有授權的掃描與館藏 provenance |

## 本輪重要訂正

1. 已知正式發售軟體是 F001–F012，固定 MAME snapshot 表示十二款皆已 dump。
2. 本地 `Super Dragon Force` ZIP 內容實為 F007 `Super Light Saga - Dragon Force／超級光明戰史`。
3. UM6618 target 是**四個 normal layers＋ROZ**；目前 oracle 只實作三個 normal layers。
4. `$F001F0` 是 pixel／GFX mode，不是 FRC；FRC control/frequency 位於 `$E90014/$E90016`。
5. 主 68k IRQ1–7 的 MAME 作者觀察可補成 expansion、cart、FRC/timer、horizontal retrace、
   fixed-line trigger、sound-to-main、vertical retrace，但仍屬研究觀察，不是晶片資料表。

## 網路資料已接近停止線的項目

以下缺口目前找不到可直接升格的公開資料；繼續搜尋一般規格網站預期收益很低：

- UM6618／UM6619 完整 register manual、netlist／Verilog；
- UM70C188 原廠資料表與 command／direct-color programming sequence（已找到的是 UM70C171）；
- 16000-2A 額外 128 KiB VRAM 的 register／renderer／DMA consumer（最高位配線已知）；
- UM6650 `$09/$0C` 到 cartridge pins 的完整時序；
- FRC 真實公式、UM6619 envelope／release 與類比混音增益。

這些應轉向 ROM consumer、實機 logic analyzer、卡帶／主機板走線或晶粒逆向，不應用二手規格表
反覆互引。現階段最能提升模擬器品質的文件工作，是把十二款 catalog notes 轉成逐遊戲可重播
驗證矩陣。
