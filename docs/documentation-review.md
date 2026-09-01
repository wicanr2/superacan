# 文件完整度複查與可補來源

更新日期：2026-09-01（第二輪複查）。此表以「能否支持軟體模擬」為準，不以頁數或未命名 register 數量評分。

| 文件領域 | 現況 | 本輪找到的補強來源 | 下一個有效動作 |
|---|---|---|---|
| BIOS／IPL | 完整涵蓋固定 dump、vectors、控制流與 hash | MAME ROM definitions | 只剩 invalid-key 動態實驗與其他 revision provenance |
| 正式軟體目錄 | 本輪補齊 F001–F012、標題、serial、hash、NVRAM 提示 | MAME `hash/supracan.xml`（CC0） | 對本地九款建立正常玩家路徑矩陣 |
| UM6618 | 位址骨架完整；第四層、pixel/gfx mode、window／IRQ 定義本輪補強 | MAME driver 作者 `hw_docs/pergame.md` `1b9e8fe` | 以 F003/F005/F007 的 consumer 驗證第四層、priority、ROZ／window |
| UM6619 | 主要 PCM／DMA／timer 可實作 | MAME sound device＋本地遊戲 driver | envelope／release 仍需實機或更多 driver consumer |
| UM70C188 | 型號／接線已知；F003 `$0001/$0009` 動態切換、`$27EE` shadow 與 runtime 解壓 producer 已確認 | Bitsavers UMC datasheet＋`PPU.sch`＋ROM＋6000-frame oracle trace | 形式化 F003 解碼格式並做同 save-state bit 3 A/B，才能判斷 direct-color |
| 卡帶／SRAM | raw ROM、雙 part、32 KiB fallback 已知 | MAME software list＋板級 schematic | 實拍各型卡帶 PCB，確認哪些 serial 真有 SRAM／電池 |
| 主機板 | 16000-2A schematic 已證實 UM6618 `VRAM_A17` 接 SRAM `A16` | `superacan-notes` `PPU.sch` | 以 ROM consumer／logic capture 找出誰產生最高位；不再把配線列為未知 |
| 類比輸出 | 元件與近似邊界已知 | UM70C171、KA2195D datasheet | 要精確只能量測 UM70C188／實機 composite capture |
| 歷史／發售資料 | 基本年份與發行商可由 catalog 固定 | MAME software list | 當年新聞／廣告仍需有授權的掃描與館藏 provenance |

## 2026-08-31 輪次的重要訂正

1. 已知正式發售軟體是 F001–F012，固定 MAME snapshot 表示十二款皆已 dump。
2. 本地 `Super Dragon Force` ZIP 內容實為 F007 `Super Light Saga - Dragon Force／超級光明戰史`。
3. UM6618 target 是**四個 normal layers＋ROZ**；目前 oracle 只實作三個 normal layers。
4. `$F001F0` 是 pixel／GFX mode，不是 FRC；FRC control/frequency 位於 `$E90014/$E90016`。
5. 主 68k IRQ1–7 的 MAME 作者觀察可補成 expansion、cart、FRC/timer、horizontal retrace、
   fixed-line trigger、sound-to-main、vertical retrace，但仍屬研究觀察，不是晶片資料表。
6. F003 的兩段 `$F001F0` producer 並非兩次獨立 copy：兩者同屬 `$73B44–$74BEB`
   壓縮區解至 `$FFFFB800–$FFFFDC55` 的單次連續輸出；格式細節與 bit 3 畫面因果仍未定案。

## 2026-09-01 第二輪複查的訂正

1. **`umc6650` 埠角色沒有分歧。** 先前六處文件寫「MAME `umc6650.cpp` 埠角色寫反、
   MAME 為何仍能開機待查」。MAME 以 `umask16(0x00ff)` 掛在 `$EB0D00–$EB0D03`，
   device offset = bus 位址>>1，因此 offset 1 就是 `$EB0D03`（位址埠）、offset 0 是
   `$EB0D01`（資料埠），與 IPL／Bcan 一致；原斷言把 bus 位址當成 device offset。
   相關敘述已從 memory-map、bios-68k、chip-emulation-guide、
   hardware-implementation-sources、emulation-readiness-assessment、emulator-analysis
   與 AGENTS 移除。
2. **Formosa Duel 的卡帶入口是 `$00002416`**（原記 `$00000426`）；SSP `$00FCFEFC` 正確。
   其餘七款與 F007 part 0 的向量已逐一重算相符。
3. **sound RAM 的容量落差首次明確記錄**（memory-map.md §5.1）：`APU.sch` 只有
   `SNDRAM_A0..A14`（32 KiB），而位址空間、68k 視窗與三個模擬器實作都是 64 KiB。
4. **`$E90000–$E9001F` 逐暫存器並列**（memory-map.md §2.1）：`$E90010` = IRQ mask
   （bit7 vblank IRQ7、bit4 可視線 IRQ4）；`$E90014/16` 的 FRC 與 DMA 位址兩套解讀
   並列，附四個 ROM 具名寫入點；`$E90018` 的 RNG 與取樣播放位置兩套解讀並列。
5. **UM6618 `$0A`／`$0C`** 補為 raster line-on／line-off 觸發（→ 68k IRQ5）；
   `$00` 的讀取語意（bit15 vblank 區間、bit1 奇數幀、讀取解除 IRQ7）取代原本
   「vblank = IRQ4？」的疑問。
6. **65C02 NMI 來源定案為主機 vblank**（`$E90010` bit7 成立時與 68k IRQ7 同時發出），
   sound-driver.md §2／§2.2 的「待查證」撤除。
7. `bios-65c02.md` 殘留的「byte 對調寫入 65C02 端」與 `emulator-analysis.md` §4.6 把
   `$E90004/05`、`$E9000C` 稱為手把埠，兩處已對齊既有定案。
8. 手把按鍵對應取得獨立佐證：`superacan-notes` 作者以自製轉接板實測 SNES 手把協定相同、
   只有命名不同，與 memory-map.md §7 的位元序吻合。
9. 引用 MAME FRC case table 時要注意其 period 因運算子優先序實際只等於 `frequency`。

10. **`$E90014/16/18` 定案為同一個計數器**（memory-map.md §2.1）：Speedy Dragon 的
    「設週期→啟動→IRQ3 handler 累加 `$FCE00E`→等待迴圈」閉合了計時器語意；Formosa Duel
    把 `$E90018` 讀值加到 tilemap 1 的 scroll 並用兩次讀值拼亂數種子。Bcan 的 DMA 位址／
    取樣播放位置命名是同一顆計數器的別名。真實週期公式仍未知。
11. **sound RAM 32 KiB alias 假說做過一次 A/B**（memory-map.md §5.1）：四款 ROM 各 1200 幀，
    除 Boom Zoo 約 0.01% 音訊樣本外全部相同；唯一對撞點是 Boom Zoo 的 `$040A/$040B`。

12. **F003 pixel-mode bit 3 的 oracle 邊界已釐清**（f003-video-mode.md §7）：Bcan 每幀由
    `sub_140082130` 建立 snapshot 供 renderer `sub_14009D6E0` 使用；該建構器以一次 8-byte
    讀取取得 `video+588..595`，只取用低 4 byte（video flags 與圖層致能），**pixel mode 與
    gfx mode 兩個 byte 未進入 snapshot**。因此 Bcan 的 renderer 結構上不依賴 `$F001F0`，
    MAME 亦然。軟體 oracle 無法回答此題，下一步只剩實機訊號量測。
13. **Bcan 的 sound RAM 模型已由反編譯確認**（memory-map.md §5.1）：65C02 側以未遮罩的
    16-bit 位址索引同一塊緩衝區、I/O 只在 `$0400–$04FF` 攔截，68k 側轉發完整位址，
    存檔序列化 `0x10000/0x10000/0x8000` 三塊。即 Bcan 假設 64 KiB、無 A15 alias。

外部來源複查：`supracan.cpp`、`umc6650.cpp`、`umc6619_sound.cpp` 的固定 commit `6ae579a`
與 2026-09-01 的 master 逐 byte 相同；`superacan-notes` 仍為 `63731a2`、`angelosa/hw_docs`
仍為 `1b9e8fe`。固定引用有效，不需重查；可補的內容都在已固定的原始碼裡。

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
