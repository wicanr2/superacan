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
| `$E80000–$E8FFFF` | 音效共享 RAM 視窗（64 KB，68k 以 16-bit 存取；**不做 byte 對調**，(a) 遊戲驅動實測，見 sound-driver.md；word-swap 只存在於 ROM 檔案格式層）。實體裝片只有 32 KiB，落差見 §5.1 |
| `$E90000–$E9001F` | UM6619 主機端埠（sound host port）；逐暫存器見 §2.1 |
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

### 2.1 UM6619 主機端埠 `$E90000–$E9001F`（(b) MAME master／(a) Bcan）

MAME 與 Bcan 對同一組埠有部分不同命名；下表把兩邊並列，衝突項另於表後說明。

| 位址 | MAME `host_um6619_map` (b) | Bcan SystemBus (a) |
|---|---|---|
| `$E90004/05` | 讀 sound RAM `$040C/$040D`（65C02 交出的取樣 DMA 請求位址） | 讀取閂（物件 +5168/+5169） |
| `$E9000A/0B` | 寫入 → 置 65C02 IRQ bit5（命令通知） | 觸發 SoundHostPort 虛函式 |
| `$E9000C/0D` | 讀 sound RAM `$040A`（DMA 請求旗標）；註記 staiwbbl 清掉 `$E8040A` 後預期讀到 `$FF` | 讀取閂（+5170） |
| `$E90010/11` | **IRQ mask**：bit7 致能 vblank IRQ7、bit4 致能可視線 IRQ4；其餘位元未知，遊戲多以 byte 寫入。註記 slghtsag 在 BIOS 之後必須設 bit7，否則 address error | 讀寫（+300450 與 +168024 雙寫） |
| `$E90014/15` | **FRC control** | 16-bit DMA 位址暫存器（+168020） |
| `$E90016/17` | **FRC frequency** | 16-bit DMA 位址暫存器（+168022） |
| `$E90018/19` | 讀回 `soundcpu total_cycles % 0xFFFF`；註記 formduel 用它捲動雨層，視為亂數源 | **DMA 取樣播放位置**（依模式即時計算，clamp 到 `$E90016` 值） |
| `$E9001C/1D` | bit3→hiview lockout、bit2→internal ROM lockout?、bit1→loview lockout、bit0 sound reset | overlay 控制（`sub_1400A3610`）；bit1/bit3 為單向 latch (a) |

**`$E90014/$E90016/$E90018` 是同一個計數器（(a)，2026-09-01 由 ROM producer／consumer 定案）。**
三款遊戲的用法互相印證：

- **Speedy Dragon**：`$30CE` `move.w d0,$E90016` 接 `$30D4` `move.w #$A200,$E90014`，
  是「以 d0 設週期並啟動」的小常式；卡帶 IRQ3 向量指向 `$3454`，內容是
  `addq.b #$1,$FCE00E` + `rte`，而 `$30DE` 是 `tst.b $FCE00E` / `beq` 的等待迴圈——
  計時器語意在軟體層閉合。另一組模式在 `$346E`（週期 0）＋`$3476`（control `$A0D6`）。
- **Formosa Duel**：`$5EB4` 寫 control `$A000`、`$5EBC` 寫週期 `$FFFF`（其 IRQ3 向量只是
  `rte`），並在 `$6076`／`$607E` 連讀兩次 `$E90018` 用 `swap` 拼成 32-bit 存進 `$FFFF28`
  （亂數種子的形狀），又在 `$868A`／`$8696` 把讀值加到 `$F00124`／`$F00126`
  （tilemap 1 的 scrollx／scrolly）——與 MAME 註解「formduel 用它捲動雨層」完全對上。
- **Journey to the Laugh**：`$FC6AC` 寫週期 `$8FC`、`$FC6B4` 寫 control `$A0D6`，接著
  `$E90010=$C0C0` 並把 SR 降到 `$2000`；全 ROM 有 22 處讀 `$E90018`。

因此 `$E90014` 是計數器控制、`$E90016` 是週期／重載值、`$E90018` 讀回目前計數值，
到期拉起 68k IRQ3。MAME 的 FRC 命名成立；Bcan 把 `$E90014/16` 標成 DMA 位址暫存器、
把 `$E90018` 標成取樣播放位置，是同一個計數器的另一種命名（它 clamp 到 `$E90016` 的行為
正好等於「計數不超過週期」）。

### 2.2 週期公式（a，Bcan 反編譯定案）

`$E90014` 寫入進 `sub_1400A7420`、`$E90016` 進 `sub_1400A7510`，兩者算同一件事：

```text
control 高位元組必須是 $A2，否則計數器停用（$A3 與其他值都是停用）
n = $E90016
interval = ceil(N × (n + 1) / D)          單位：主時脈 tick
  control & $0F == $0 → interval = 107,386,350（＝整整一秒，與 n 無關）
  control & $0F == $1 → N = 1024 × 107,386,350，D = ⌊107,386,350 / 12⌋ → ≈ 12,288 × (n+1)
  control & $0F == $F → N = 9040 × 107,386,350，D 同上          → ≈ 108,480 × (n+1)
  其他                → 停用
```

反編譯裡的三個常數 `0x199A57B800`、`0xE2068E6460`、`8948862` 拆開來就是
`1024 × master`、`9040 × master` 與 `⌊master/12⌋`——master 會約掉，剩下純 tick 數。
因此**計數器的輸入時脈是 master/12 ＝ 8.9488625 MHz**，模式 `$1` 每 1024×(n+1) 個輸入
tick 觸發一次、模式 `$F` 每 9040×(n+1) 個。除法取天花板，所以 Bcan 的值會比整數倍多 1。

換算頻率：模式 `$1`、n=0 為 8,739.12 Hz；模式 `$F`、n=0 為 989.92 Hz；模式 `$0` 為 1 Hz。

本地實測沒有任何遊戲用模式 `$1` 或 `$F`：Speedy Dragon 寫 `$A200`（模式 `$0`，
週期暫存器 `$013A` 因此無效）＋另一次 `$A0D6`（高位元組不是 `$A2`，停用）；
Formosa Duel 寫 `$A000`（停用）。也就是說**唯一被啟用過的設定是「每秒一次」**，
與 Speedy Dragon 的 IRQ3 handler 累加 `$FCE00E` 的計時器語意吻合。

絕對單位（主時脈 tick）是由常數結構推出的**強推論**：`N/D` 的形式讓 master 約掉，只有
把結果讀成 tick 數才自洽。真正把它釘死需要看 Bcan 排程器如何消費 `counter+32`，
或在實機上量。

引用 MAME FRC case table 時另注意：`update_frc_state` 的 period 寫成
`m_frc_control & 0xff << 16`，依 C++ 運算子優先序等於 `control & 0x00ff0000`，對 16-bit
的 `m_frc_control` 恆為 0，因此其**實際 period 只等於 `frequency`**，不是註解暗示的 24-bit
組合值。MAME 自己也把整段標為未解出的 HACK。

## 3. UM6618 視訊暫存器（b，基址 $F00000，offset 為 byte）

| Offset | 功能 |
|---|---|
| `$00` | Video IRQ flags／status（讀：bit15=目前在 vblank 區間、bit1=奇數幀；讀取即解除 vblank IRQ7）。IRQ level 對照見 §6 |
| `$02` | 目前掃描線（讀） |
| `$0A` | Raster「line on」觸發：bit15 啟用＋低 8 bit 目標線號，到線時拉起 68k **IRQ5** |
| `$0C` | Raster「line off」觸發：同格式，到線時解除 IRQ5 |
| `$08` | video flags：bit11 interlace、bit10 global double-height、bit9 overscan（224/240）、bit8 h256/h320；bit7–4 normal layer 1–4、bit3 sprite、bit2 ROZ、bit1/0 window clip 1/2 enable |
| `$10–$1E` | Sprite DMA：count、dest MSW/LSW、src inc、src MSW/LSW、control |
| `$20/$22/$24/$26` | sprite base addr（word index ＝值×2）、sprite count（+1）、mono color、flags（bit0：8bpp/4bpp）。表項目 4 word 的逐欄位語意、縮放與 mosaic 公式見 [sprite-format.md](sprite-format.md) |
| `$100–$10E` | Tilemap 0：tile mode、scrollx、scrolly、base addr（<<1）、mode、linescrollx addr、lineselect addr |
| `$120–$12E` | Tilemap 1（同格局） |
| `$140–$14E` | Tilemap 2（同格局） |
| `$160–$17E` | Tilemap 3／第四 normal layer（MAME 作者逐遊戲筆記已觀察；目前 driver／本地 oracle 尚未接入） |
| `$180–$19E` | ROZ 層：mode、tile mode、scrollx/scrolly（32-bit）、係數 A/B/C/D、map base、tile bank／bitmap base、3 個逐行參數表位址。逐暫存器解碼見 §3.1 |
| `$1D0–$1DE` | Window 0/1：control、start addr、scrollx、scrolly |
| `$1F0` | pixel mode（bit4-3）＋GFX mode（bit2-0）；F003 實際在 `$0001/$0009` 間切換 bit3；`$E90014/$E90016` 不在 UM6618 window，其 FRC／DMA 位址兩套解讀見 §2.1 |

Tilemap flags：bit15-13 優先度、bit11-8 尺寸（16×16/32×32/64×32/128×32/64×64
tile）、bit5 wrap、bit4-2 mosaic、bit1/0 全層 X/Y flip。
硬體 target：4 個 normal tilemap + 1 個 ROZ + sprite + 2 個 window；色深 8/4/2/1 bpp。
固定 MAME driver 與本地 C++ oracle 目前只實作前三個 normal layers。第四層與 `$1F0` bitfield
來自 MAME driver 作者的逐遊戲 register observation
[`pergame.md`](https://github.com/angelosa/hw_docs/blob/1b9e8fe813b29f196ff04ca9c194319ced779f4c/funtech_superacan/pergame.md)，
證據層級仍是研究觀察，不是原廠資料表。

### 3.1 ROZ 暫存器的解碼倍率（a，Bcan `sub_1400A9200`）

Bcan 在寫入時就把部分 ROZ 暫存器換算成內部位址，倍率不一致，逐條列出以免誤植：

| 暫存器 | 內部欄位 | 換算 | 用途 |
|---|---|---|---|
| `$180` | +544 | 原值 | mode：bit15-13 優先度、bit11-8 尺寸、bit5 wrap、bit4-2 mosaic 表選擇、bit1-0 region |
| `$182` | +546 | 原值 | tile mode：bit15／bit14／bit6 選逐行表路徑，低 4 bit 為 bitmap 模式的 palette bank |
| `$184`／`$186` | +550／+548 | 原值 | scroll X（24-bit 有號，`$186` 為高位） |
| `$188`／`$18A` | +554／+552 | 原值 | scroll Y |
| `$18C`–`$192` | +556–+562 | 原值 | 係數 A／B／C／D（8.8 定點） |
| `$194` | +564 | **×2** | tilemap map base，最終 byte 位址再 ×2 |
| `$196` | +568 | 原值 | tile bank（renderer 取 bit15-12）；bit 3 的 bitmap 模式以其 **×4** 為 byte 基底 |
| `$198`／`$19A`／`$19E` | +572／+576／+580 | **×4** | 三個逐行參數表位址 |

`$F001F0` bit 3 造成的 ROZ bitmap 路徑（公式、指令位址與自製 ROM 驗證）見
[f003-video-mode.md](f003-video-mode.md) §7.3、§7.6。

## 4. DMA（a）

- 主機 DMA **2 通道**（非外界流傳的 8 通道；8 之說 **待查證**，MAME 只實作
  ch0/ch1，位於 `$E90020/30`）。
- 每通道暫存器：source MSW/LSW、dest MSW/LSW、count、control；搬 `count + 1` 個單位。
- control `& $8800` 不為 0 才觸發；`bit12`=word、`bit10`=dest 遞減、`bit9`=src 遞減、
  `bit8`=word 模式下 dest 每 16 byte 回捲；`$A800`（相等比對）是寫 0／byte 的特例分支。
- 完整位元表、傳輸後的暫存器狀態、逐 byte 量測與一處回讀差異見
  [host-dma.md](host-dma.md)。
- 另有 **sprite DMA**（UM6618 內部，`$F00010` 起）。

## 5. 65C02（音效 CPU）側（b）

- 完整 64 KB 位址空間對映到共享 sound RAM；68k 端經 `$E80000` 存取同一 RAM。
  實體裝片只有 32 KiB，落差與 alias 推論見 §5.1。
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

### 5.1 位址空間 64 KiB 與實體裝片 32 KiB 的落差（未定案）

65C02 的位址空間、68k 的 `$E80000–$E8FFFF` 視窗、MAME `sound_map`（`0x0000–0xffff` 一整塊
share）與 Bcan、superacan-emu 的配置都是 **64 KiB**。板級證據只有 **32 KiB**：`APU.sch` 的
U11 是單顆 `UM62256`（32K×8），逐 net 檢查只有 `SNDRAM_A0..A14`，整份 schematic 沒有
`SNDRAM_A15`（(p)，`superacan-notes` 固定 commit `63731a2`）。兩者要同時成立，只能是 65C02
的 A15 沒有接到 SRAM，上半 32 KiB 是下半的 alias。

軟體證據與該推論相容，並指出一個具體後果：八款本地 ROM 的 word-swap 還原映像都出現
32-bit 值 `$00E88400`（byte-pattern 掃描，未逐一反組譯確認全部是 operand），而 Boom Zoo
把歌曲位址表複製到 65C02 `$8400` 已由反組譯確認（sound-driver.md §4.1）。若 alias 成立，
`$8400` 實際落在實體 `$0400`——正好是被 I/O 頁蓋住、無法由 `$0400` 觸及的那 256 bytes，
因此 `$8400` 會是使用該塊 RAM 的唯一視圖，而 I/O 解碼必須看 A15。

**A/B 實驗（2026-09-01，software-observed）**：在 superacan-emu 加入只對 RAM 存取丟掉 A15
的診斷模式（I/O 解碼仍用完整 65C02 位址）後，Boom Zoo、Monopoly、Speedy Dragon、
Formosa Duel 各跑 1200 幀完整 BIOS 路徑。兩種模型下 68000／65C02 指令數、`vram_sha256`、
`framebuffer_sha256` 與 IRQ ack 計數完全相同；唯一差異是 Boom Zoo 的音訊
（`audio_nonzero` 453046 → 453000，約 0.01% 樣本）。

同一輪的對撞偵測（記錄同一實體 cell 先後被上下半區寫入）給出更精確的定位：Monopoly、
Speedy Dragon、Formosa Duel 為零；Boom Zoo 恰好兩個 cell —— `$040A`／`$040B`，也就是
65C02→68k mailbox 旗標與該遊戲複製到 `$8400` 起的歌曲位址表（sound-driver.md §4.1）
在 alias 模型下會共用同一塊儲存。

**Bcan 的模型已由反編譯確認為 64 KiB、不做 A15 遮罩（a）**（IDA Pro 9.4／Hex-Rays）：

- 65C02 側的 bus 存取是 `sub_1400A59C0`（讀）與 `sub_1400A5220`（寫），兩者以完整 16-bit
  位址 `switch`，`$0400–$04FF` 逐一列為 I/O case（`$0407`、`$040A`、`$0420`、`$0422`…），
  其餘走 `default:`，內容為
  `*(BYTE *)(*(QWORD *)(obj + 16) + a2)`——**用未遮罩的 16-bit 位址直接索引同一塊緩衝區**。
  因此在 Bcan 裡 `$8400` 是 RAM、`$0400` 是 I/O，與 alias 模型的 A15 假設方向一致，
  但上下半區是各自獨立的儲存。
- 68k 側：`SystemBus` 以 `(addr & 0xFF0000) == 0xE80000` 判斷後把**完整位址**轉給
  SoundHostPort（`sub_1400A23A0`／`sub_1400A27F0`）；位址分類器 `sub_1400A3430` 對該區段
  保留的 offset 是 `addr − $E80000`，同樣沒有遮到 15 bit。
- 即時存檔的機器區段（magic `ACMS`）連續序列化三塊記憶體：`0x10000`、`0x10000`、`0x8000`，
  與 Work RAM 64 KiB＋sound RAM 64 KiB＋卡帶 SRAM 32 KiB 相符（VRAM 另在別處，大小 `0x20000`）。

Bcan 對所有邊界操作都會「stopped safely」，而遊戲持續存取 `$8000` 以上的 sound RAM 位址，
若緩衝區只有 32 KiB 早就會被它自己的邊界檢查擋下。因此可確定：**Bcan 假設 64 KiB、無 alias**。
這說明沒有任何一款遊戲「需要」alias 才能運作，但不能反過來證明實機就是 64 KiB——
Bcan 的硬體層本來就移植自 MAME，兩者共用同一個假設。

**實作契約（2026-09-01 定案）**：跟隨 Bcan——**64 KiB 平面、不遮罩 A15**，
`$0400–$04FF` 以完整 65C02 位址解碼為 I/O。這是 `confirmed-Bcan` 等級的實作決定，
不是 `confirmed-hardware`；硬體側仍未定案，唯一可量測的分歧點是 Boom Zoo 的
`$840A/$840B`。要升格成硬體事實，必須在實機同一狀態下寫入 `$8400+n` 之後看
`$E9000C`／`$E8040A` 讀回什麼。在那之前不改模型，也不把 32 KiB 假說列為錯誤。

## 6. 中斷（(b) MAME driver＋(a) 實作驗證）

- 68k：**IRQ1**=expansion、**IRQ2**=cartridge、**IRQ3**=FRC timer（`$E90014/16`，見 §2.1；Speedy Dragon 的 `$3454` handler 與等待迴圈已
  在軟體層證實）、
  **IRQ4**=UM6618 可視線（vpos<240，需 `$E90010` bit4）、**IRQ5**=UM6618 line-on／line-off
  觸發（`$F0000A`／`$F0000C`）、**IRQ6**=sound CPU→main mailbox（65C02 寫 `$040A`）、
  **IRQ7**=vertical retrace（vpos 240，需 `$E90010` bit7）。IRQ1／IRQ2 尚無本地 consumer。
  level 名稱出自 MAME 作者 `pergame.md` 的 research observation，但 IRQ4／5／7 的致能條件與
  觸發點可直接對到 driver 程式碼，並已由 superacan-emu 實跑（IRQ7 真實受理）。
- vblank 那一刻（`$E90010` bit7 成立時）除了 68k IRQ7，MAME 同時對 65C02 送一次 **NMI**，
  註記「staiwbbl requires this for inputs to work」。這就是遊戲 65C02 驅動裡讀 `$0412`
  作 ack 的那條 NMI（sound-driver.md §2、§2.2）。
- 65C02：單一 IRQ 線，6 來源 bitmap 在 `$0411`（見 §5）。

## 7. 手把硬體位元序（b，16-bit active low）

bit15=A、bit14=B、bit13=Start、bit12=Select、bit11=Up、bit10=Down、
bit9=Left、bit8=Right、bit7=X、bit6=Y、bit5=L、bit4=R、bit3-0 未用。

- 官方手把為方向 + Start/Select + **A/B/X/Y/L/R**（SFC 式配置）。
- 獨立佐證：`superacan-notes` 作者以自製轉接板實測 SNES 手把可直接使用，序列協定相同、
  只有按鍵命名不同（A↔SNES B、B↔SNES Y、Start↔SNES Select、Select↔SNES Start、
  X↔SNES A、Y↔SNES X、L／R 同名）。該對照與上面的位元序完全吻合。
- Bcan 介面以 A/B/C/X/Y/Z 命名六鍵，其 C/Z 對應硬體 L/R 為**強推論**（鍵數與順序相符），
  不是實機絲印證據。

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
- **Bcan 實作 (a)（2026-08-30，SystemBus 反編譯）**：`$EB0D03` 寫入位址埠
  （7-bit）、`$EB0D01` 讀寫資料埠，金鑰區 `$20–$2F` 唯讀（讀取自
  `umc6650.bin`）、RAM 區 `$40–$5F` 可讀寫。MAME device 以 `umask16(0x00ff)`
  掛 `$EB0D00–$EB0D03`，其 device offset = 位址>>1，offset 1 即 `$EB0D03`
  （位址埠）、offset 0 即 `$EB0D01`（資料埠），與 IPL／Bcan 相同；三者無分歧。
  同一個 byte-lane 慣例也出現在卡帶 SRAM（Bcan 的 `index = addr>>1`）。
