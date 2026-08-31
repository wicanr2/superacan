# Super A'Can 記憶體映射與硬體暫存器

> 來源層級說明（AGENTS.md §7）：
> **(b)** = MAME driver `src/mame/umc/supracan.cpp`（Angelo Salese /
> Ryan Holtz，BSD-3-Clause；2026-08-31 重查 commit
> `6ae579aed3107c0b42c1c1c5cb05c02df4456eff`）。
> **(a)** = Bcan.exe 逆向實測（見 [emulator-analysis.md](emulator-analysis.md)）。
> 兩者衝突時以 (a) 為準並記錄。

## 1. 時脈（(a) 定案，推翻 (b)）

- 主振盪器 U13 = **53.693175 MHz**（MAME 註解；Bcan 內出現整數常數
  53693175，(a) 確認）。
- **Bcan 實測時脈模型（(a)，IDA 反編譯，見 emulator-analysis.md §4.1）**：
  master tick = **107.38635 MHz**（2 × U13）；**68k = 10.738635 MHz**
  （master tick /10，即 U13/5，流傳值）；**65C02 = 3.579545 MHz**
  （master tick /30，流傳值；整除關係 3579545 × 30 = 107386350 成立）。
- **與 MAME 矛盾**：MAME 設 68k = U13/6 ≈ 8.95 MHz、65C02 = U13/6/2 ≈
  4.47 MHz（自註 TODO 未驗證）。以 (a) 為準：Bcan 採用流傳值
  10.74/3.58 MHz，MAME 的 /6、/12 應視為未定案猜測。
- UM6619 音效：`XTAL(3'579'545)`（b），與上述 65C02 時脈一致。
- 螢幕時序：`U13 / 10`，342×262（b）；Bcan 顯示幀率基準 60 Hz
  （snapshot 驗證函式內 ÷60，(a)），狀態列自稱「native 320x240 video」(a)。

## 2. 68000 位址空間（b：MAME `main_map`）

| 位址範圍 | 內容 |
|---|---|
| `$000000–$3FFFFF` | 卡帶 ROM（低區視圖）；`$000000–$000FFF` 開機時覆疊 `internal_68k.bin`（4 KB IPL） |
| `$E80000–$E8FFFF` | 音效共享 RAM（64 KB，68k 以 16-bit 存取；**不做 byte 對調**，(a) 遊戲驅動實測，見 sound-driver.md；word-swap 只存在於 ROM 檔案格式層） |
| `$E90000–$E9001F` | UM6619 主機端埠（sound host port，含 6502 來的 DMA 請求位址） |
| `$E90020–$E9002F` | DMA 通道 0 暫存器 |
| `$E90030–$E9003F` | DMA 通道 1 暫存器 |
| `$E90B3C–$E90B3D` | lockout 檢查時的雜訊區（NOP） |
| `$EB0D00–$EB0D03` | **UMC6650** lockout/安全晶片（8-bit，umask16 0x00ff） |
| `$EC0000–$ECFFFF` | 卡帶 NVRAM/SRAM（8-bit 寬） |
| `$F00000–$F001FF` | **UM6618** 視訊暫存器（256 個 16-bit 暫存器窗口） |
| `$F00200–$F003FF` | 調色盤 RAM，256 色 × xBGR-555 |
| `$F40000–$F5FFFF` | **68k 可見 VRAM 視窗 128 KiB**；`PCGAM 16000-2A` 物理裝片合計 256 KiB，UM6618 可驅動上半部但 consumer 未定 |
| `$F80000–$FBFFFF` | 卡帶 ROM（高區視圖），`$F80000–$F80FFF` 同樣可覆疊 IPL |
| `$FC0000–$FCFFFF` | **Work RAM 64 KB**，`mirror(0x30000)` → `$FC/FD/FE/FFxxxx` 皆映射同一 RAM |

- Work RAM `$FC0000–$FCFFFF`（64 KiB）另獲 **(a) 級確認**：Bcan cheat 搜尋
  明確限制「Only game RAM FC0000-FCFFFF (64 KiB) is searched」。
- **全表已獲 (a) 級確認（2026-08-30，IDA 反編譯 SystemBus 四個讀寫分派函式，
  見 emulator-analysis.md §4.2）**，包括：SRAM 僅奇位址有效、
  `$F00400–$F3FFFF` 與 `$F60000–$F7FFFF` 靜默 no-op、Work RAM 實際以
  addr & 0xFFFF 映射（$FC–$FF 四頁同體）、越界 ROM 讀回 0xFFFF 不丟
  BusError、`$E90018` 回報 DMA 取樣播放位置、`$E9001C/1D` 為特殊控制。
- mirror 0x30000 解釋了 ROM 向量表中出現 `$00FFxxxx` 形式 SSP 的現象
  （見 [bios-rom-format.md](bios-rom-format.md)）。
- 卡帶 SRAM 固定 32768 bytes 另獲 (a) 確認（Bcan 卡帶存檔必須恰好 32768 B）。
- **物理 VRAM 與 CPU 視窗須分開**：早期板級筆記記錄兩顆 `UM61512`
  （合計 128 KiB），`PCGAM 16000-2A` 的照片／電路圖則是兩顆 `UM611024`
  （合計 256 KiB）。`PPU.sch` 已確認 UM6618 `VRAM_A17` 直連兩顆 SRAM `A16`，所以上半部
  可被視訊 ASIC 實際定址；仍未證實其 register／renderer／DMA consumer，也未證實 CPU
  window bank switching。詳見 [vram-architecture.md](vram-architecture.md)。

## 3. UM6618 視訊暫存器（b，基址 $F00000，offset 為 byte）

| Offset | 功能 |
|---|---|
| `$00` | Video IRQ flags（讀）；寫入控制中斷（vblank = 68k IRQ4？IRQ 來源見 §6） |
| `$02` | 目前掃描線（讀） |
| `$08` | video flags：bit11 interlace、bit10 global double-height、bit9 overscan（224/240）、bit8 h256/h320；bit7–4 normal layer 1–4、bit3 sprite、bit2 ROZ、bit1/0 window clip 1/2 enable |
| `$10–$1E` | Sprite DMA：count、dest MSW/LSW、src inc、src MSW/LSW、control |
| `$20/$22/$24/$26` | sprite base addr（<<2）、sprite count（+1）、mono color、flags（bit0：8bpp/4bpp） |
| `$100–$10E` | Tilemap 0：tile mode、scrollx、scrolly、base addr（<<1）、mode、linescrollx addr、lineselect addr |
| `$120–$12E` | Tilemap 1（同格局） |
| `$140–$14E` | Tilemap 2（同格局） |
| `$160–$17E` | Tilemap 3／第四 normal layer（MAME 作者逐遊戲筆記已觀察；目前 driver／本地 oracle 尚未接入） |
| `$180–$19E` | ROZ 層：tile mode、scrollx/scrolly（32-bit）、係數 A/B/C/D、base addr、tile bank、3 個逐行參數表位址 |
| `$1D0–$1DE` | Window 0/1：control、start addr、scrollx、scrolly |
| `$1F0` | pixel mode（bit4-3）＋GFX mode（bit2-0）；FRC control/frequency 是 `$E90014/$E90016`，不在 UM6618 window |

Tilemap flags：bit15-13 優先度、bit11-8 尺寸（16×16/32×32/64×32/128×32/64×64
tile）、bit5 wrap、bit4-2 mosaic、bit1/0 全層 X/Y flip。
硬體 target：4 個 normal tilemap + 1 個 ROZ + sprite + 2 個 window；色深 8/4/2/1 bpp。
固定 MAME driver 與本地 C++ oracle 目前只實作前三個 normal layers。第四層與 `$1F0` bitfield
來自 MAME driver 作者的逐遊戲 register observation
[`pergame.md`](https://github.com/angelosa/hw_docs/blob/1b9e8fe813b29f196ff04ca9c194319ced779f4c/funtech_superacan/pergame.md)，
證據層級仍是研究觀察，不是原廠資料表。

## 4. DMA（b）

- 主機 DMA **2 通道**（非外界流傳的 8 通道；8 之說 **待查證**，MAME 只實作
  ch0/ch1，位於 `$E90020/30`）。
- 每通道暫存器：source MSW/LSW、dest MSW/LSW、byte count（+1）、control。
- control `bit15 或 bit11` 觸發；`bit10`=dest 遞減、`bit9`=src 遞減；
  `0xA800` 為特殊填充/位元組模式（staiwbbl 開機用）；`bit12` 為 word 模式，
  `bit8` 間接模式（往 `$F00010–$1F` 埠連寫時 dest 每 16 byte 回捲）。
- 另有 **sprite DMA**（UM6618 內部，`$F00010` 起）。

## 5. 65C02（音效 CPU）側（b）

- 完整 64 KB 位址空間對映到共享 sound RAM；68k 端經 `$E80000` 存取同一 RAM。
- I/O 暫存器在 **`$0400–$04FF`**：

| 位址 | 功能 |
|---|---|
| `$0300` | Boot OK 狀態 |
| `$0402/$0403` | 手把 shift register 0/1（讀） |
| `$0404/$0405` | 68k→65C02 byte latch ×2（IRQ bit3/bit2）：**空讀回 `$CD`**；68k 經 `$E80404/$E80405` 窗口寫入即置位並觸發 IRQ；65C02 讀取即 ack 並清空（(a)，superacan-emu 實測修正；MAME 當作純 RAM、無 IRQ） |
| `$0406` | 手把 +5V presence?（讀） |
| `$0407` | 手把 shift register 控制（寫：latch/移位/清除，雙手把）；清除脈衝（bit4/5）同時觸發對應 latch IRQ（功能推測 (a)，probe 快速路徑所需） |
| `$0409` | IRQ 來源 bit4 ack（讀取 ack，(a) 遊戲驅動實測，與 (b) 一致） |
| `$040A` | 6502→68k IRQ 請求（mailbox；觸發 68k IRQ6）；**65C02 讀取 = ack IRQ bit5**（(a)，兩套驅動的 bit5 handler 實測） |
| `$040C/$040D` | (a) 取樣 DMA 位址/半頁資訊交給 68k（寫後 `$040A=$FF` 觸發 68k IRQ6 refill，雙緩衝 PCM 串流，見 sound-driver.md） |
| `$0410` | IRQ enable |
| `$0411` | IRQ 來源旗標（**純狀態、讀取不清**，(a) superacan-emu 實測修正）：各 bit level-held 直到專屬 ack——0x40←讀 UM6619 reg `$16`、0x04←讀 `$0405`、0x08←讀 `$0404`、0x10←讀 `$0409`、0x20←讀 `$040A`、0x80←讀 reg `$14`。MAME 的「讀取即清全部」會丟同時發生的來源 |
| `$0412` | NMI acknowledge |
| `$0420` | UM6619 暫存器位址（寫）/音效硬體狀態（讀） |
| `$0422` | UM6619 暫存器資料（讀寫） |

- 手把為**序列移位**介面：16-bit，經 `$0407` latch 後逐位移入
  `$0402/$0403`；68k 也可從 sound RAM `$0200/$0202` 直接讀到已組合的
  手把狀態（active low，`^ 0xFFFF`）。
- UM6619：暫存器間接定址（addr=$0420、data=$0422）；reg $14/$16 與
  timer/DMA IRQ 相關。**暫存器語意已升級為 (a)**（Speedy Dragon 驅動
  實測 + superacan-emu 里程碑 3 實作驗證，見 [sound-driver.md](sound-driver.md)
  §5）：`$17`=key on/off（高 nibble≠0=key-on、低 nibble=通道）、
  `$20–$2F`/`$30–$3F`=通道 period 低/高（addr_increment=period<<6，
  16.16 固定小數點）、`$50–$5F`=波形長度（0x40<<n，bit0=one-shot）、
  `$60/$70`=取樣起始位址（×0x40）、`$90–$9F`=DMA 驅動旗標（雙緩衝，
  播完觸發 IRQ bit6 並自動重新 key-on）、`$E0–$EF`=通道音量（高/低 nibble
  左右聲道 ×17）、`$11/$12`=timer period（10×(0x10000−n) clocks，初始值
  ≈200 Hz）、`$14`=timer 控制（bit7 啟動、bit6 致能 IRQ bit7、讀取 ack）、
  `$16`=取樣 DMA 狀態（bit6 busy、讀取 ack IRQ bit6）。合成方式：
  **PCM/取樣式，無 FM**；取樣為 sound RAM 8-bit 無號資料，原生抽樣率
  = 3.579545 MHz/80 = 44744.3125 Hz（(b) MAME `umc6619_sound.cpp` 模型，
  已獲 (a) 實作驗證）。

## 6. 中斷（b）

- 68k：**IRQ1**=expansion、**IRQ2**=cartridge、**IRQ3**=UM6619 host/FRC timer、
  **IRQ4**=UM6618 horizontal retrace、**IRQ5**=UM6618 fixed-line trigger、
  **IRQ6**=sound CPU→main mailbox、**IRQ7**=UM6618 vertical retrace。
  IRQ3–7 有多款 ROM handler／mask 使用觀察；IRQ1/2 尚無本地 consumer。來源為 MAME 作者
  `pergame.md`，仍標 (b) research observation，而非 confirmed-hardware。
- 65C02：單一 IRQ 線，6 來源 bitmap 在 `$0411`（見 §5）。

## 7. 手把硬體位元序（b，16-bit active low）

bit15=A、bit14=B、bit13=Start、bit12=Select、bit11=Up、bit10=Down、
bit9=Left、bit8=Right、bit7=X、bit6=Y、bit5=L、bit4=R、bit3-0 未用。

- 即官方手把為方向 + Start/Select + **A/B/X/Y/L/R**（SFC 式配置）。
  Bcan 介面的 C/Z 鍵對應 L/R 肩鍵的可能性 **待查證**。

## 8. UMC6650（a+b）

- MAME 掛在 `$EB0D00–$EB0D03`，装置名 `m_lockout`，註解「security
  related」——判斷為**鎖區/保護晶片**。
- Bcan 需要 `umc6650.bin`（16 bytes）；內容為 ASCII「UMC 1994 (C)」+
  4 byte（見 [bios-rom-format.md](bios-rom-format.md)）。
- 68k IPL ROM（`internal_68k.bin`）在 MAME 註解同樣標「security
  related」。
- **協定已由 IPL 反組譯釐清 (a)**（見 [bios-68k.md](bios-68k.md) §3）：
  `$EB0D03`（寫）= 內部位址埠、`$EB0D01`（讀寫）= 資料埠；內部
  `$20–$2F` 為 16 byte 金鑰（`umc6650.bin`）、`$40–$5F` 為 RAM、`$09/$0C`
  為輸出給卡帶的 lockout 結果。
- **差異 (b vs a) 已定案（2026-08-30，Bcan SystemBus 反編譯）**：Bcan 實作為
  `$EB0D03` 寫入位址埠（7-bit）、`$EB0D01` 讀寫資料埠，金鑰區 $20–$2F
  唯讀（讀取自 umc6650.bin）、RAM 區 $40–$5F 可讀寫——與 IPL 實際用法一致，
  **確認 MAME `umc6650.cpp` 的埠角色寫反**（MAME 能開機的原因仍待查）。
