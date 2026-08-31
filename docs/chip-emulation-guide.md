# Super A'Can 逐晶片模擬實作指南

本文件把[硬體組成與參考來源](hardware-implementation-sources.md)進一步落成可實作的
模擬契約。位址與位元定義仍以 [memory-map.md](memory-map.md) 為準，音效 mailbox 與
遊戲驅動資料流以 [sound-driver.md](sound-driver.md) 為準。

目前實作證據來自本機 `superacan-emu` 里程碑 1–4、Bcan 反編譯 (a)，並以固定版 MAME
`6ae579a` (b) 交叉驗證。這是功能層模擬，不宣稱晶片內部 netlist 或逐電氣週期一致。

## 1. 整機排程與資料流

主排程器以 68k 已執行週期為單調時間基準：

```text
執行一條 68000 指令
  → 取得本次增加的 68k cycles
  → 每累積 3 cycles 推進 65C02 1 cycle
  → 同步推進 UM6619 timer 與取樣器
  → 累積到每掃描線 budget 後推進 UM6618 vpos
  → 在 raster／vblank／mailbox／timer 事件更新 IRQ 線
```

- 68k 為 **10.738635 MHz**，65C02 為 **3.579545 MHz**，比例正好 3:1 (a)。
- 一幀採 262 線；目前 320 模式每線 728 個 68k cycle、256 模式 684 個 cycle，240 線進
  vblank 並產生 framebuffer。這是目前可運行的 (a)+(b) 模型，不是示波器證實的光柵時序。
- 68k IRQ 優先順序目前為 vblank 7、sound mailbox 6、視訊 IRQ5、raster 4、FRC 3。
  採 HOLD_LINE：CPU 真正受理該 level 後才解除來源，不能每輪主迴圈先清除。
- 匯流排必須提供 8/16-bit 原子存取。會觸發 DMA 的 word register 不可拆成兩次 byte write，
  否則會重複啟動 DMA。

## 2. MC68HC000P10 主 CPU

目前以 Moira 的 `M68000` model 實作；MAME m68000 core 也是可替代選項。

1. CPU core 的 byte/word/long read/write callback 全部導向 24-bit `SystemBus`。
2. reset vector 初期由 4 KiB IPL overlay 提供；UMC6650 與卡帶授權通過後，`$E9001C`
   bit1/bit3 只允許由開到關，形成單向 latch。遊戲稍後把 register 寫回 0 不得恢復 overlay。
3. `willInterrupt`／interrupt acknowledge callback 通知平台解除對應 HOLD_LINE；不要讓 CPU core
   自己猜哪個週邊已完成 acknowledge。
4. 即時存檔需保存 CPU core 的完整執行狀態，而不只是可見暫存器；否則例外、STOP 或半條
   micro-operation 附近無法可靠恢復。

## 3. W65C02 音效與輸入 CPU

目前以 CLK `6502Mk2::WDC65C02` 執行，每個 bus transaction 回傳一個 cycle。

### 3.1 reset／HALT

CLK 的 Reset 是 level-sensitive，且 CPU 有真正取得 cycle 才會捕捉。UM6619 端 HALT 期間仍須
推進 timer／audio，但不可推進 65C02。重新釋放時要維持 Reset 線，直到觀察到 CPU 讀
`$FFFC` reset vector 才解除；目前另設 64-cycle safety bound。先設再立刻清 Reset，或固定只跑
7 cycle，都會截斷 reset sequence，Speedy Dragon 第二音樂驅動會因此停擺。

### 3.2 IRQ 與 I/O

六個來源採 bitmask 保存並共同驅動 level IRQ，各來源只能由自己的讀取端解除：

| IRQ bit | 來源／ack |
|---|---|
| 2 | 讀 `$0405` |
| 3 | 讀 `$0404` |
| 4 | 讀 `$0409` |
| 5 | 讀 `$040A`，68k mailbox 命令 |
| 6 | 讀 UM6619 reg `$16`，DMA／取樣完成 |
| 7 | 讀 UM6619 reg `$14`，timer |

`$0411` 只是狀態讀回，不能仿照舊 MAME 行為在讀取時清掉所有 IRQ。`$0404/$0405` 是 latch，
空值讀回 `$CD`。手把則把 active-low 16-bit 狀態在控制線 falling edge latch，再 MSB-first shift；
模擬的是 74LS164 等邏輯的可見契約，不需逐閘模擬。

## 4. SystemBus、RAM、卡帶與 DMA

- bus 先把位址遮成 24 bit，再分派 IPL／ROM、Work RAM、sound RAM、SRAM、UM6650、UM6618、
  UM6619 bridge 與控制暫存器。未映射及 ROM 越界讀回 `$FF/$FFFF`。
- 64 KiB Work RAM 依 `$FC0000–$FCFFFF` 映射；32 KiB battery SRAM 保持 8-bit、奇位址契約。
- 卡帶為 raw word-swapped image；不做 mapper。雙部分卡帶在 loader 層組成同一邏輯映像。
- 主 DMA 保存 source、destination、count、control，再依 word/fill、source/destination decrement 與
  16-byte destination wrap 位元搬運。目前共有兩通道；未知 control 組合應停止或記錄，不應猜補。
- state 必須一併保存 RAM、DMA、overlay latch、IRQ pending 與週期餘數，避免 restore 後事件漂移。

## 5. UMC6650 卡帶 lockout

UMC6650 可用很小的狀態機表示：256-byte 內部空間、7-bit address latch，以及外部提供的
16-byte key。

1. `$EB0D03` 寫入選擇 address，`$EB0D01` 讀寫 data；此角色已由 IPL/Bcan (a) 證實，與
   MAME 現有 device 的 offset 解讀相反。
2. key 放在內部 `$20–$2F` 並設唯讀；`$40–$5F` 是 32-byte RAM。
3. 其他已觀察位址先保存 readback，讓 IPL 的 `$09/$0C` 交握成立；其外部 pin 電氣語意仍未知。
4. 驗證 gate 是 IPL 完成交握、比對卡帶 `$2000` 授權資料並跳到卡帶向量，不是只測 register
   round-trip。

## 6. UM6618 視訊 ASIC

目前採「register state → indexed layers → priority compose → palette conversion」模型：

```text
CPU 寫 UM6618 registers / 128 KiB 可見 VRAM / 256-entry palette
  → 解碼三個 tilemap、ROZ、sprite、window 與 DMA 狀態
  → 逐像素取 8×8 packed 8/4/2-bpp tile
  → 在 indexed framebuffer 合成各層及 sprite priority
  → 以 xBGR555 palette 轉成 320×240 RGBX8888
```

### 6.1 圖層

- 目前 oracle 的三個 tilemap 支援尺寸、signed scroll、wrap、全層／tile flip、mosaic、linescroll、lineselect、
  8/4/2-bpp 與 palette bank。像素 0 依色深 mask 視為透明。
- 硬體 register observation 顯示另有 `$F00160–$F0017F` 第四 normal layer；它尚未進入
  oracle，應以 F007 等實際 consumer 建立 READY spec 後實作。
- ROZ 使用 24.8 scroll 與 8.8 A/B/C/D fixed-point，每像素累加來源座標；另保留遊戲使用的
  per-line parameter table。開機 logo 的 1-bpp alternate layout 以 VRAM write 時同步建立的地址
  重排副本讀取。
- sprite table 每筆 4 word，支援 direct／子 tile table、尺寸、bank、flip、palette、priority 與
  mask buffer；sprite DMA 由專屬 register block觸發。
- window 0 依每行 min/max clip 表繪製。window 1 的對稱實作目前是保守假說，尚無遊戲路徑
  證實，不能列為 confirmed parity。

### 6.2 顯示與中斷

- 由最低 priority 7 往最高 0 合成 tilemap、ROZ、window，再以 sprite priority 比較覆蓋。
- palette entry 為 `xBGR555`；目前直接擴為 8-bit RGB。UM70C188 DAC 與 KA2195D NTSC encoder
  不需出現在一般 framebuffer path，因此這只是 digital color approximation。
- 若要新增可選的類比輸出 path，可參考同族 UM70C171 的 256×18-bit palette、pixel mask、
  `BLANK` 與三路 6-bit DAC pipeline，再接 KA2195D 的 RGB／sync 輸入；但在 UM70C188 相容性
  未證實前，這只能標為研究模式，不能取代已驗證的 `xBGR555` framebuffer path。
- vpos、奇偶幀、vblank／raster pending 都屬 device state；讀取特定 status register 或 68k
  interrupt acknowledge 才解除對應事件。

仍未知：16000-2A 額外 physical VRAM 的內部 consumer（`VRAM_A17` 配線已確認）、精確 color mix、部分 sprite clipping／scaling、第二
window 與部分 ROZ table。應以具名遊戲畫面建立窄測試，不用 SFC／Mega Drive 行為補洞。

## 7. UM6619 音效 ASIC

UM6619 目前建模成 16-channel sample synthesizer，加 timer 與 DMA completion IRQ：

1. reg `$20–$3F` 組合 pitch，換成 16.16 address increment `pitch << 6`。
2. reg `$50–$5F` 設定 `0x40 << n` 長度與 one-shot；`$60–$7F` 設起址，單位 0x40 byte。
3. reg `$E0–$EF` 將左右聲道各 4-bit volume 擴成 8 bit；reg `$17` key-on/off。
4. 每 80 個 3.579545 MHz cycle 產生一個 stereo sample，即 **44,744.3125 Hz**。
5. sound RAM 的 unsigned 8-bit PCM 轉成 signed 16-bit，依 16.16 phase 取樣、乘左右音量、混合
   active channels、保留 headroom 後 clamp。
6. 抵達 end address 時依模式 one-shot stop、loop，或在 DMA channel 產生 IRQ bit6 並重新 key-on，
   讓 65C02 驅動完成雙緩衝補資料。
7. timer period 目前為 `10 × (0x10000 - value)`；enable 後到期拉起 IRQ bit7。

宿主輸出把原生 44.744 kHz PCM 以線性插值轉成 48 kHz，再送 SDL2 或 WAV。這屬重製的
hardware-spec approximation；不模擬 LF347 類比濾波、KA2195D 音訊 buffer 或逐波形實機輸出。
reg `$A0–$DF` envelope 目前僅保存 readback、未套用；`superacan-web` 對高通道做人工 decay 的
方法是消噪 heuristic，不能當作 ADSR 證據。

## 8. 驗證與完成判準

| 層級 | 最小驗證 |
|---|---|
| CPU／bus／UM6650 | IPL 交握、授權比對、overlay 關閉後到達兩款以上卡帶入口 |
| UM6618 | 開機 logo，加至少兩款遊戲的 tilemap、sprite、ROZ／window 抽樣與畫面 checksum／截圖 |
| 65C02／UM6619 | 一般及第二驅動 reset、mailbox ack、六 IRQ 不互相吞掉、PCM 非靜音且時長合理 |
| 輸入 | shift 與 direct path 各一款，正常標題畫面按 Start 後狀態確實改變 |
| state | 指令邊界擷取、ROM hash、transactional restore，恢復後畫面／音訊／IRQ 可重現 |

測試通過只證明上述玩家路徑與目前模型一致。未經實機邏輯分析、晶片 decap 或更多 ROM consumer
證實的內部行為，仍須保留 (b)、strong inference 或 hypothesis 標記。

晶粒逆向方面，UM6619 已有「走線與 cell boundary 約完成 99%」的公開進度說明，但 cell 邏輯
尚未完成辨識，SiliconRE 仍將 UM6618F／UM6619F 標為 Stalled；在公開 schematic／netlist 出現前，
不能把這項進度當作閘級 oracle。現階段仍以遊戲 driver 的 register consumer 與玩家路徑驗證為主。
