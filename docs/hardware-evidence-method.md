# 由板級接線確認晶片機制的方法與盤點

更新日期：2026-08-31。本文件回答「能否像 VRAM `A17` 一樣，由晶片腳位與主機板接線確認
其他機制」。答案是可以，但接線只證明外部拓撲；客製 ASIC 內部 register、時序與演算法仍需
軟體 producer／consumer、動態 trace 或實機量測。

## 1. 證據鏈

每項機制依下列順序交叉確認，不因腳位名稱看似明確便直接升格：

1. 固定主機板 revision 與 schematic commit，記錄實體晶片型號、pin 與 net；
2. 對標準晶片查原廠資料表，以 truth table／bus cycle 解釋接線；
3. 對客製 ASIC 保留原 pin 名，只把「誰和誰相連」列為板級證據（p）；
4. 從 BIOS、卡帶 ROM 或音效 driver 找 register 的寫入端與資料格式；
5. 與 Bcan（a）、MAME（b）或實機 logic trace 比對副作用與時序；
6. 文件同列原始定位、語意、推論等級及證據，不以自訂名稱取代原 net。

## 2. 逐晶片可確認程度

| 晶片／電路 | schematic 可直接確認 | 還需要什麼 | 可達成程度 |
|---|---|---|---|
| MC68HC000P10 | 24-bit address、16-bit data、`AS/UDS/LDS/RW`、`IPL0..2`、bus arbitration、reset／halt 接到系統 ASIC／插槽 | CPU datasheet、Bcan clock、ROM exception／IRQ consumer | CPU core 與外部 bus cycle 可完整實作 |
| U1/U2 Work RAM | 2×32K×8＝64 KiB；U1 接 D0–7、U2 接 D8–15；`WRAM_LCS/HCS` 由 UM6619 產生 | bus decode/readback trace 確認 mirror 與 wait state | 容量、lane 與邏輯映射已足夠 |
| U5/U6 VRAM | 2×128K×8＝256 KiB；UM6618 獨占 `A0..A16`、D0–15、OE／WE，兩顆 CE 固定有效 | ROM／renderer／DMA trace 找 `VRAM_A17` consumer | 實體拓撲完整，內部位址來源部分未知 |
| U11 sound RAM | 32K×8；`A0..A14`、D0–7、WE、CE/OE 全由 UM6619 直接控制（全圖無 `SNDRAM_A15`） | 65C02 memory cycle、68k window 與 DMA arbitration trace；上半 32 KiB 是否為 alias | 容量與 ownership 完整；與 64 KiB 位址空間的落差見 [memory-map.md](memory-map.md) §5.1 |
| UM6618 | 直接接 CPU bus、完整 VRAM bus、UM70C171 palette DAC、master clock、UM6619／卡帶／手把訊號 | 十二款 ROM register producer、renderer trace、實機 video／IRQ capture | 外部介面可固定；tile／sprite／ROZ／IRQ 內部規則需逐功能驗證 |
| UM6619 | 直接接 CPU bus、控制 68k reset/halt/arbitration/IRQ、Work RAM selects、sound RAM、手把、stereo analog 與 UM6618／卡帶訊號 | 65C02 driver、MAME sound core、Bcan trace、analog capture | 可確認它兼具 system controller／APU／I/O；PCM register 與 IRQ 多數可實作 |
| UM6650 | 卡帶 bus 與 lockout 相關 pins、16-byte key dump | 68k IPL producer／consumer、Bcan ports、實機量測 `$09/$0C` 外部 pins | 開機授權行為足夠；完整電氣協定仍不完整 |
| 74F08/74F32/74LS164/7406/74F14 | 每個 gate 與 controller pin 的完整連線 | 標準 74xx truth table、UM6619 I/O 時序 | 可重建 shift／latch 行為，不必逐 transistor 模擬 |
| U3 `UM70C188` RAMDAC | UM6618 的 D0–7、RS0/1、RD/WR、PCLK、BLANK 與 P0–7 連線 | UM70C171 pin-compatible datasheet、UM70C188 command／pixel-mode trace | indexed palette 可做；特殊 direct-color path 待證 |
| LF347 與輸出網路 | UM6619 `AUDIO_L/R` 到放大／濾波元件的路徑 | 元件值、實機增益／頻率響應量測 | 可做合理混音近似，不足以宣稱逐波形一致 |

## 3. 本輪由接線升格的結論

### 3.1 UM6619 是主要 bus／memory controller

`APU.sch` 顯示 UM6619 不只是音效晶片。它接收完整 CPU A1–A23、D0–D15 與
`AS/UDS/LDS/RW`，並連到 `DTACK`、`VPA`、`BR/BG/BGACK`、`IPL0..2`、reset 與 halt。
此外，Work RAM 的 `WRAM_LCS/HCS` 及 sound RAM 的全部控制線均由它輸出。故模擬器把
SystemBus arbitration、Work RAM byte lane、65C02／sound RAM ownership 放在 UM6619 邊界，
有明確板級依據；各 register decode 與 cycle timing 則仍以 Bcan／ROM trace 為準。

### 3.2 SRAM 組織可直接排除容量傳聞

- Work RAM：兩顆 `UM62256` 各 32K×8，合成 32K×16＝64 KiB；不是 256 KiB。
- Sound RAM：一顆 `UM62256`，32K×8＝32 KiB；只有 `A0..A14` 進入該晶片，65C02 的 64 KiB
  位址空間因此上下半疑為 alias（[memory-map.md](memory-map.md) §5.1）。
- 16000-2A VRAM：兩顆 `UM611024`，128K×16＝256 KiB；詳見
  [vram-architecture.md](vram-architecture.md)。

容量與 byte lane 可由料號、地址線及資料線共同確認；mirror／bank 等邏輯仍由 ASIC decode
決定，不能只從 SRAM 容量推導。

### 3.3 手把 glue logic 最適合此方法

`PAD.sch` 把兩顆 `74LS164` shift register 與 `74F08/74F32/7406/74F14` 的 gate 級連線完整
列出，並連回 UM6619 的 `JOY1_LATCH/DATA/CLK` 及第二埠相關 pins。配合標準元件 truth table
即可建立可測的 serial latch／shift 契約；這類外部離散邏輯比 UM6618 內部 rendering 更適合
由 schematic 直接重建。

## 4. 不可由接線單獨確認的項目

下列資訊即使 net 全部已知，也不能只靠「同系列 CPU／相似主機」補出：

- UM6618 register bit、layer priority、ROZ scaling、sprite clipping、VRAM `A17` 的內部來源；
- UM6619 PCM envelope、timer 精確公式、IRQ ack 副作用、DMA completion timing；
- UM6650 `$09/$0C` 的完整外部電氣時序；
- 兩顆客製 ASIC 間未命名 pins（如 `6619_29`）的方向、封包與時序；
- palette DAC、音訊放大器與 NTSC encoder 的逐波形輸出。

U3 的詳細證據與 `$F001F0` 特殊像素模式假說見 [palette-dac.md](palette-dac.md)。

這些項目應改用「接線限定候選範圍，再由 ROM consumer／Bcan trace／實機量測定案」，不可把
Mega Drive、Neo Geo 或其他 Motorola 68000 平台的客製 ASIC 行為直接移植。

## 5. 來源

- [splash5/superacan-notes schematics（固定 commit）](https://github.com/splash5/superacan-notes/tree/63731a2202ffa1ad829c49da8804a05b07a5943b/schematics)：`CPU.sch`、`PPU.sch`、`APU.sch`、`PAD.sch`、`PCCAR_16003-1B.sch`（p）。
- 本庫 [memory-map.md](memory-map.md)、[sound-driver.md](sound-driver.md) 與
  [emulator-analysis.md](emulator-analysis.md)：Bcan／ROM／MAME 的 producer-consumer 證據。
