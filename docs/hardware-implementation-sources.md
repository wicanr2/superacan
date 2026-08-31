# Super A'Can 硬體組成與模擬實作參考

本文件回答兩個問題：Super A'Can 主機板上有哪些主要元件，以及重製模擬器時每一部分
可以參考哪個公開實作。它是元件與來源索引；暫存器的原始位址仍以
[memory-map.md](memory-map.md)為準，音效命令與資料流以
[sound-driver.md](sound-driver.md)為準。
實際排程、reset、IRQ、像素合成與 PCM 演算法見
[逐晶片模擬實作指南](chip-emulation-guide.md)。
現有資料能支持的模擬器完成層級、MAME source 定位與缺口見
[軟體模擬資料充分度評估](emulation-readiness-assessment.md)。

## 1. 證據契約與本次網路快照

除本庫既有的 (a) Bcan／BIOS／ROM 實測、(b) MAME 實作、(c) 二手資料外，本文件使用：

- **(p) 板級證據**：實機照片、晶片絲印、PCB 走線或依走線重建的電路圖。它可證明裝片、
  接腳與連線，不能單獨證明暫存器或遊戲行為。
- **資料表**：晶片原廠文件可證明該料號的一般介面；仍須以 (p) 證明主機實際使用方式。
- **參考實作**：只代表可閱讀或重用的程式，不自動升格成原機事實。與 (a) 衝突時以 (a) 為準。

2026-08-31 固定檢查的原始碼快照：

| 來源 | Commit | 授權 | 用途 |
|---|---|---|---|
| [MAME](https://github.com/mamedev/mame/tree/6ae579aed3107c0b42c1c1c5cb05c02df4456eff/src/mame/umc) | `6ae579aed3107c0b42c1c1c5cb05c02df4456eff` | BSD-3-Clause | 整機、UM6618、UM6619、UM6650、卡帶與 CPU 核心整合 |
| [splash5/superacan-notes](https://github.com/splash5/superacan-notes/tree/63731a2202ffa1ad829c49da8804a05b07a5943b) | `63731a2202ffa1ad829c49da8804a05b07a5943b` | MIT | `PCGAM 16000-2A` PCB 照片、CPU／PPU／APU／PAD／卡帶電路圖、UM6650 替代板 |
| [anomixer/superacan-web](https://github.com/anomixer/superacan-web/tree/929e51c00bdf9475f9bca9f319acf338eb4de4ea) | `929e51c00bdf9475f9bca9f319acf338eb4de4ea` | repo 未見頂層 LICENSE，個別 MAME 衍生碼仍受原授權約束 | MAME WebAssembly 整合與實驗性音效修正 |

另以 [Emmanuel Vadot 的板級筆記](https://gist.github.com/evadot/66cfdb8891544b41b4c9)
交叉比對較早主機板元件；MAME 原始碼也將此筆記列為參考。

## 2. 主機板主要元件

以下料號來自 `PCGAM 16000-2A` 電路圖及板照 (p)。「模擬必要」是指數位模擬器是否需要
呈現玩家可見行為，不代表可忽略實機維修研究。

| 位置／元件 | 實機角色與已知連線 | 模擬必要性 | 證據與限制 |
|---|---|---|---|
| U9 `MC68HC000P10` | 16/32-bit 68000 系列主 CPU；16-bit data、24-bit address bus | 必要 | `CPU.sch` 絲印／符號 (p)；Bcan 核心與時脈為 (a) |
| U12 `UM6618` | 視訊／系統 ASIC；接 CPU bus、VRAM、palette DAC、主振盪器及 UM6619 訊號 | 必要 | `PPU.sch` (p)；暫存器主要來自 MAME (b) 與 Bcan (a) |
| U10 `UM6619` | 音效、W65C02 執行環境、sound RAM、手把／IRQ／DMA 與類比音訊介面 | 必要 | `APU.sch` (p)；音效模型及遊戲驅動資料流為 (a)+(b) |
| U3 `UM70C188` | palette／三路 DAC 介面；早期板級筆記稱與 `UM70C171` 同類 | 數位色彩必要；類比波形可近似 | `PPU.sch` 與早期板級筆記 (p)；未找到 UM70C188 原廠資料表或獨立公開模擬器 |
| U4 `KA2195D` | Samsung NTSC RGB encoder，接 RGB、composite sync、音訊 buffer 與 composite output | 一般 framebuffer 模擬可省略；精確 composite 輸出才需要 | `PPU.sch` (p)；[KA2195D 資料表](https://consolemods.org/wiki/images/8/87/KA2195D.PDF) |
| U13 `53.693175 MHz` oscillator | 主振盪器 MCLK | 必要 | `PPU.sch`／板照 (p)；CPU 分頻以 Bcan (a) 為準，不採 MAME TODO 值 |
| U1/U2 `UM62256` | 兩顆 32K×8，組成 64 KiB、16-bit Work RAM | 必要 | `CPU.sch` (p)；`$FC0000–$FCFFFF` 為 (a) |
| U11 `UM62256` | 一顆 32K×8 sound RAM | 必要 | `APU.sch` (p)；65C02 映射與 mirror 行為為 (a)+(b) |
| U5/U6 `UM611024`（16000-2A） | 各 128K×8，物理裝片合計 256 KiB、16-bit VRAM | 必要 | `PPU.sch`／板照 (p)；CPU 視窗只有 128 KiB，額外容量的選擇方式未知 |
| U14 `LF347` | 四路 JFET op-amp，音訊類比放大／濾波 | 通常可省略 | `APU.sch` (p)；數位模擬輸出 PCM 後由宿主混音 |
| U16/U17/U18/U19/U20/U21 | `74F08`、`74F32`、兩顆 `74LS164`、`7406`、`74F14`；手把 shift／buffer 邏輯 | 需重現行為，不需逐閘模擬 | `PAD.sch` (p)；可直接實作 16-bit latch／shift 契約 |
| 卡帶 `UM6650` | 16-byte key ROM、32-byte RAM 與授權／lockout 輸出 | 開機必要 | 卡帶電路圖 (p)、IPL (a)、MAME device (b)；MAME 埠角色有已知錯誤 |
| 卡帶 `62256`＋CR2032 | 可選 32 KiB、8-bit battery-backed SRAM | 有存檔遊戲時必要 | 卡帶電路圖 (p)、Bcan 固定映像大小 (a) |
| 電源與類比輸出 | 兩組 7805 rail、AV／RF／stereo RCA、power switch | 邏輯模擬通常省略 | `MISC.sch`／`PPU.sch` (p) |
| 擴充 edge connector | CPU／UM6618／UM6619 部分 bus 與 audio signal 外露；沒有上市周邊 | 目前不阻塞 | `CPU.sch` (p)；周邊協定仍未知，不應猜補 |

### 2.1 VRAM revision 差異

較早的板級筆記把 U5/U6 記為兩顆 `UM61512`（各 64K×8，合計 **128 KiB**）；
`PCGAM 16000-2A` 的照片與電路圖則標示兩顆 `UM611024`（各 128K×8，物理合計
**256 KiB**）。因此目前只能分開陳述：

1. 68k 的 `$F40000–$F5FFFF` 可見視窗是 **128 KiB**，已由 Bcan 與 MAME bus map 支持；
2. 至少一個 `16000-2A` revision 的物理 VRAM 裝片容量是 **256 KiB**；
3. 額外位址是否供 UM6618 內部 bank、ROZ、sprite 或其他用途，**未知**；在追出選擇端與
   consumer 前，不可把 256 KiB 全部暴露成線性 68k VRAM。

Work RAM 的早期板筆記使用 `W24257S`，16000-2A 圖則使用 pin-compatible `UM62256`；
兩者組織均為 32K×8，故不改變已確認的 64 KiB 邏輯容量。

## 3. 逐晶片模擬實作參考

| 子系統 | 優先參考 | 可重用範圍 | 必須修正／不可照抄之處 |
|---|---|---|---|
| 整機與 SystemBus | [MAME `supracan.cpp`](https://github.com/mamedev/mame/blob/6ae579aed3107c0b42c1c1c5cb05c02df4456eff/src/mame/umc/supracan.cpp) | 位址骨架、視訊/DMA/IRQ、輸入、machine config | MAME 仍把 68k/65C02 設為 U13/6、U13/12；應改用 (a) 的 10.738635／3.579545 MHz。IRQ ack、UM6650 埠、部分 DMA/ROZ/window/priority 也有已知 TODO |
| 68000 CPU | [Moira](https://github.com/dirkwhoffmann/Moira)（MIT）或 [MAME m68000 core](https://github.com/mamedev/mame/tree/6ae579aed3107c0b42c1c1c5cb05c02df4456eff/src/devices/cpu/m68000)；介面查 [Motorola/NXP M68000 manual addendum](https://www.nxp.com/docs/en/reference-manual/M68000UMAD.pdf) | 指令、例外、中斷 ack；Bcan 已使用 Moira | 型號設定為 68000／MC68HC000 相容模式；主機 overlay、bus 與 HOLD_LINE IRQ 屬平台 glue，不在 CPU core 內 |
| W65C02 CPU | [CLK](https://github.com/TomHarte/CLK)（MIT）的 6502Mk2，或 [MAME W65C02 core](https://github.com/mamedev/mame/tree/6ae579aed3107c0b42c1c1c5cb05c02df4456eff/src/devices/cpu/m6502)；介面查 [WDC W65C02S datasheet](https://www.wdc65xx.com/wdc/documentation/w65c02s.pdf) | CMOS 65C02 指令、cycle 與 interrupt | CLK reset 為 level-sensitive；HALT 期間不可吞掉 reset sequence。IRQ 六來源為平台 level-held，不能在 CPU core 外一次清空 |
| UM6618 | MAME `supracan.cpp` 的 `video_r/video_w`、tilemap、ROZ、sprite、window 與 DMA | 目前唯一找到的公開完整數位實作骨架 | 尚非獨立 device；MAME 自述需重寫。第四層、ROZ scaling table、sprite sizing/clipping、priority、color mix 與 secondary window 仍有 TODO；只能把已驗證路徑移植成 READY 規格 |
| UM6619 | [MAME `umc6619_sound.cpp`](https://github.com/mamedev/mame/blob/6ae579aed3107c0b42c1c1c5cb05c02df4456eff/src/mame/umc/umc6619_sound.cpp)／[header](https://github.com/mamedev/mame/blob/6ae579aed3107c0b42c1c1c5cb05c02df4456eff/src/mame/umc/umc6619_sound.h) | 16 PCM voices、pitch、wave address/length、stereo volume、timer、DMA IRQ、44.744 kHz stream | envelope 4 bytes、reg `$09/$15/$16` 與 DMA completion 仍部分未知；須以本庫遊戲驅動分析修正。`superacan-web` 的 channel 11–15 人工 decay 是消噪 heuristic，不是硬體 ADSR 證據 |
| UM6650 | [MAME `umc6650.cpp`](https://github.com/mamedev/mame/blob/6ae579aed3107c0b42c1c1c5cb05c02df4456eff/src/mame/umc/umc6650.cpp)＋[splash5 替代板研究](https://github.com/splash5/superacan-notes/tree/63731a2202ffa1ad829c49da8804a05b07a5943b) | 16-byte ROM key、`$40–$5F` RAM、7-bit address latch | 以 IPL/Bcan (a) 為準：`$EB0D03` 是位址、`$EB0D01` 是資料；MAME `read/write(offset)` 角色相反。`$09/$0C` 輸出仍未完整建模 |
| 卡帶／SRAM | [MAME Super A'Can bus](https://github.com/mamedev/mame/tree/6ae579aed3107c0b42c1c1c5cb05c02df4456eff/src/devices/bus/supracan) | raw `.bin`、越界讀 `0xFFFF`、battery save | MAME 只接受單檔 `.bin` 骨架；Bcan 的雙部分卡帶、word-swap 載入與固定 32768-byte SRAM 契約須另補 |
| Palette／UM70C188 | MAME `palette_device::xBGR_555` | 256-entry digital palette 與 framebuffer 色彩 | 這只是玩家畫面近似，不是 UM70C188 類比 DAC 的電氣模擬 |
| KA2195D | Samsung 資料表；若只輸出 RGB framebuffer 可不建 device | 想模擬 NTSC composite 時參考 pin、carrier、sync、RGB matrix | 不應把一般 CRT shader 稱為 KA2195D 精確模擬；目前沒有找到 Super A'Can 專用公開實作 |
| 手把 | MAME input/shift code＋`superacan-notes` 的 SNES adapter mapping | latch、clock、16-bit active-low shift stream | A'Can 與 SNES 的 A/B/X/Y、Start/Select mapping 不同；Bcan UI 的 C/Z 名稱也不能當實機按鍵絲印 |

### 3.1 UM70C188／UM70C171 的可用邊界

[UM70C171 原廠資料表](https://www.bitsavers.org/components/umc/UM70C171.pdf)描述的是
256×18-bit color palette、每色 6-bit 的三路 DAC、pixel address／color value／pixel mask register，
並有 `BLANK`、pixel clock 與類比 RGB 輸出。這能提供宿主若要重建 palette DAC pipeline 時的
介面範例，但目前只能列為**同族參考**：

- 板級筆記「UM70C188 與 UM70C171 同類」不是 pin-compatible 或 register-compatible 的證明；
- A'Can 已觀察到的 256-entry `xBGR555` 寫入與畫面結果仍以 UM6618／Bcan／MAME (a)+(b) 為準；
- 不可把 UM70C171 的 18-bit palette、pixel mask register 或 6-bit DAC 精度直接宣稱為
  UM70C188 已確認規格；需要 UM70C188 資料表、走線或實機訊號才能升格。

### 3.2 `superacan-web` 的適用邊界

`superacan-web` 提供可運行的 MAME WebAssembly 封裝與 `sndfix` 成品，適合作為跨遊戲回歸
線索；但 repo 沒有完整對應的 patched C++ source，文件中的高通道音量衰減也明確屬
「實驗性 ADSR」。因此：

- reg `$16` 完成通道 status／IRQ handshake 可回到遊戲驅動與本庫 (a) 證據驗證；
- 固定對 channel 11–15 每數 frame 降音量不能視為 UM6619 hardware behavior；
- 不應直接把 wasm binary 或 heuristic 複製進乾淨重製核心。

另有 [furrtek/SiliconRE](https://github.com/furrtek/SiliconRE) 列出 UM6618F／UM6619F
晶粒逆向，但目前狀態仍為 **Stalled**。研究者在 2023 年的
[UM6619 進度說明](https://www.patreon.com/posts/super-acan-84372275)稱走線與 cell boundary 約完成
99%，同時明說後續仍須辨識 cell 功能；截至 2026-08-31，公開 repo 仍沒有可供重製直接使用的
完整 schematic、netlist、Verilog 或 emulator core。因此這是未來交叉驗證入口，不是現成實作。

## 4. 完整度與停止線

目前足以完成一般玩家路徑模擬的硬體範圍：雙 CPU、bus/overlay、RAM、卡帶、lockout、
三 tilemap＋ROZ 基本路徑、sprite、palette、主 DMA、sound RAM、16-channel PCM、手把與 IRQ。

仍須保留為未知或部分實作：

- `16000-2A` 額外 128 KiB physical VRAM 的選擇與 consumer；
- UM6618 第四層、ROZ scaling table、精確 priority/color mix、sprite edge clipping、第二 window；
- UM6619 envelope、部分 `$09/$15/$16` 位元與 DMA 邊界行為；
- UM6650 `$09/$0C` 對卡帶 pin 的完整電氣語意；
- expansion port、未上市周邊與 RF／composite 類比波形。

這些未知不應以類似主機行為猜補。只有它們阻塞具名遊戲的正常玩家路徑時，才以
「原始遊戲寫入 → 暫存器資料流 → 玩家可見結果」開新的窄 RE/spec 任務。
