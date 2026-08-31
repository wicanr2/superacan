# Bcan 0.0.8b 模擬器逆向分析

> 來源層級：除特別註明外，本文所有內容皆為 **(a) 級**——直接從 `Bcan008b/Bcan.exe`
> 的字串表、匯入表與二進位結構實測取得（2026-08-30，Linux 下以 `strings` /
> `objdump` / Python 解析 PE）。Bcan.exe 無符號表（`nm` 為空），但保留大量
> C++ RTTI mangled name 與 UTF-16 介面字串，證據力高。

## 1. 程式本體

- PE32+ GUI 執行檔（x86-64），約 5.37 MB，MinGW-w64/gcc 編譯
  （`Mingw-w64 runtime failure`、libunwind 字串）。
- 版本資訊：`FileDescription = "Bcan Super A'Can emulator"`，
  `CompanyName = "Bcan project"`，`FileVersion = 0.0.8b`。
- 作者自稱 **Billy Jr**（「Billy Jr.'s Emulator World」，About 對話框），
  自我定位：「A native Windows 11 x64 emulator dedicated to the Funtech
  Super A'Can console」，並註明非 Funtech 官方產品。
- 技術棧（由匯入 DLL 判定）：Win32 GUI + **Direct3D 11** 輸出（失敗時退回
  WARP/相容路徑）、**Windows Media Foundation**（MP4 錄影，H.264/AAC）、
  **Windows Imaging Component**（PNG 截圖）、WinMM 計時、waveOut 或
  Media Foundation 音訊、XInput（`xinput1_4.dll`）+ 通用 USB/藍牙手把。
- 內嵌資源 `.rsrc` 約 680 KB，其中一個約 616 KB 的資源（type 2, ID 0x68），
  推測為內建 UI 字型/圖像（**待查證**）。
- 介面語言：英文、法文、西班牙文、zh-TW、zh-Hans（字串中可見對應翻譯）。

## 2. 內部架構（由 RTTI mangled name 判定）

命名空間 `acan::`，C++ 模組化設計：

| 命名空間 | 類別（demangle 後） | 職責 |
|---|---|---|
| `acan::cpu` | `MoiraM68000::Impl`、`MoiraM68000SyncSink`、`MoiraM68000InterruptAcknowledgeSink`、`W65C02Bus` | 68k（Moira core）與 65C02 匯流排介面 |
| `acan::core` | `AddressBus` | 主位址匯流排 |
| `acan::hardware` | `SystemBus`、`SoundCpuBus`、`SoundHostPort`、`SoundControllerInput`、`Um6618TimingSource`、`Um6618SpriteDmaHost`、`Um6619`、`Um6619RegisterPort` | UM6618/UM6619 與音效 CPU 橋接 |
| `acan::state` | `RuntimeStateSaveResult`、`CartridgeSramSaveResult`、存檔驗證器 | save state / 卡帶 SRAM |
| `acan::session` | `MachineSession`、snapshot 驗證器 | 整機工作階段 |

- 二進位含字串「Super A'Can hardware behavior reference implementation」
  加上 BSD 3-Clause 授權（Angelo Salese、Ryan Holtz），**確認 Bcan 的硬體
  模擬層移植/改寫自 MAME `supracan.cpp` driver**；另有 Moira（MIT）與
  CLK 65C02（MIT）授權（見 `THIRD_PARTY_NOTICES.txt`）。
- 例外型別含 `moira::BusError`、`moira::AddressError`，表示 68k 匯流排錯誤
  會以例外上拋並被安全攔截。

## 3. 已確認機制

### 3.1 BIOS 載入
- 啟動時要求 `bios\supracan.zip` 與 `bios\umc6650.zip`，成員檔名、大小、
  CRC 逐一驗證（錯誤訊息：「The archive must contain exactly the expected
  Super A'Can BIOS members」、「A BIOS member does not have its exact
  hardware size」、「failed its size or CRC check」）。
- ZIP 解析為自製的「bounded」實作：拒絕 ZIP64、加密、data descriptor、
  symlink，並設壓縮比與 CPU 時間上限（防 zip bomb）。
- `internal_68k.bin` 載入後做「reset-vector interpretation」正規化
  （字串：「internal_68k.bin normalized image:」「no unique valid …
  reset-vector interpretation」）——即嘗試位元組交換解讀 68k 向量表。
- 冷開機有安全上限：「bounded BIOS boot did not reach the cartridge entry」
  表示 BIOS 必須在限定步數內跳到卡帶入口，否則拒絕啟動（防當機設計）。

### 3.2 ROM 載入
- 檔案對話框過濾器：`Super A'Can ROM (*.bin;*.zip)`。
- `.bin`：raw cartridge image；`.zip`：bounded ZIP container。
- **雙部分卡帶**：ZIP 可含兩個數字副檔名部分（`.0` + `.1`）。字串明確指出
  「Super Light Saga」需 `16007.0`（2 MiB）+ `08007.1`（1 MiB）兩個已驗證
  部分；本 repo 的 `Super Dragon Force (Taiwan).zip` 內含
  `16007 (Taiwan).bin`（2 MB）+ `08002 (Taiwan).bin`（1 MB），屬同一機制。
- ROM 以 SHA-256 正規化識別（`rom_sha256=`、`game_identifier=`，
  「The game identifier must be a lower-case SHA-256 value」），
  save state、卡帶存檔、cheat、錄影檔名都綁定此 hash。
- 卡帶存檔（cartridge save / SRAM）固定 **32768 bytes** 完整映像
  （「The cartridge save must contain exactly 32768 bytes」），
  存於 `save\`，背景 worker 寫入，失敗時阻止關閉以免遺失資料。

### 3.3 Save state（即時存檔）
- 檔案 magic：**`ACANRTS`**（ACAN RunTime State），二進位中出現兩處
  （寫入/讀取路徑各一）。
- 檔頭含版本、flags、payload 大小、所屬 ROM 的 SHA-256、整體 SHA-256
  完整性檢查（「The runtime-state integrity check failed」、
  「The runtime state belongs to a different normalized ROM」）。
- **10 個槽位（0–9）**，熱鍵循環切換（`hotkey_cycle_state_slot`，
  介面文字「Cycle save-state slot (0-9)」）。
- 只能在 CPU 指令邊界存檔（「the machine is not at a safe CPU instruction
  boundary」），背景執行緒寫檔；讀檔採 transactional restore，失敗會
  rollback，不影響進行中的遊戲。

### 3.4 Cheat（金手指）
- 內建「Memory Search / Cheat Manager」：可對 **遊戲 Work RAM
  $FC0000–$FCFFFF（64 KiB）** 做數值搜尋（精確/模糊、Changed/Unchanged/
  Increased/Decreased、16-bit/32-bit、十進位/BCD 顯示格式），候選位址
  最多顯示前 4096 筆。
- 搜尋範圍限制字串：「Only game RAM FC0000-FCFFFF (64 KiB) is searched」——
  **這是 Work RAM 位址的 (a) 級實測證據**，與 MAME driver 的
  `0xfc0000–0xfcffff` 一致。
- 每遊戲 cheat 存成 **`.cht` 檔**（per-game cheat file）。原依字串判為
  二進位格式（magic `ACAN_CHTI`），**經反編譯推翻（2026-08-30，§4.4）**：
  實為 tab 分隔純文字檔，標頭行 `BCAN_CHT_1`，讀端相容舊 magic
  `ACAN_CHT_1`。有安全大小上限與 entry 驗證。
- Cheat 可 Lock/Unlock、Write Once、全部鎖定（`hotkey_lock_all_cheats`），
  `Bcan.ini` 有 `cheat=1` 開關。

### 3.5 錄影與截圖
- 錄影兩格式：`recording_format=mp4|avi`。
  - MP4：Media Foundation H.264/AAC，檔名
    `Bcan-<rom名>-YYYYMMDD-HHMMSS-mmm.mp4`。
  - AVI：MJPEG（Windows JPEG encoder），classic RIFF 容器，
    達 **1.75 GB** 上限會安全截斷保存已完成部分。
- 截圖：PNG（WIC），存到 `Bcan.exe` 旁 `snap\` 目錄，檔名
  `Bcan-YYYYMMDD-HHMMSS-mmm.png`；FPS 顯示不會進入截圖/錄影。
- 畫面管線：原生 320×240 幀 → D3D11 呈現；濾鏡選項 Nearest（預設）、
  Bilinear、Scanline 25/50/75%、CRT Lite、CRT Full、Composite；
  整數縮放、4:3 顯示、motion smoothing。
- 除錯字串透露：「The screenshot aperture is not a valid UM6618 display
  mode」「The screenshot framebuffer is shorter than 320x240」——
  截圖直接取自 UM6618 顯示孔徑（aperture）。

### 3.6 診斷與安全設計
- **自動故障報告**「Bcan automatic fault report v1」（`.fault.txt`）：
  記錄 `rom_sha256`、`session_fault`、`cpu_fault`、`bus_fault`、
  `sound_bus_fault`、`um6619_fault`、`audio_fault`、`pc`、`opcode`、
  `master_tick`、各項影音計數器與系統資訊。表示模擬核心對未知/未移植
  硬體操作會「stopped safely」並輸出報告，而非崩潰。
- Performance diagnostic：遊玩 1–3 分鐘後輸出
  `save\Bcan-performance-diagnostic.txt`。
- Presentation trace：`presentation-trace.csv`（`presentation_trace=1`）。
- 大量「safe/safely」字樣：整機設計哲學是所有邊界檢查失敗都安全中止，
  遊戲狀態不變。

### 3.7 輸入
- 手把：方向鍵 + Start/Select + A/B/C/X/Y/Z 六鍵；鍵盤、XInput、
  通用 DirectInput 手把皆可綁定，雙人。
- `Bcan.ini` 手把 bitmask：up/down/left/right=1/2/4/8、start/select=16/32、
  y/z=256/512、a/b/c/x=4096/8192/16384/32768。
- **注意**：此 bitmask 是 Bcan 主機端（XInput 風格）編碼，**不是** A'Can
  硬體手把暫存器位元序（MAME driver 的硬體位元序見
  [memory-map.md](memory-map.md)）。

### 3.8 模擬完成度自述
- 狀態列字串：「ROM running (test build) | some ROZ/scaling/mixing
  effects are still being connected」——0.0.8b 仍有部分 ROZ/縮放/混色
  效果未接完（與 MAME driver 自述的已知問題一致）。
- 「one video frame exceeded the safe instruction limit」：每幀有指令數
  安全上限。

## 4. IDA Pro 9.4 反編譯補完（2026-08-30，(a) 級）

> 方法：IDA Pro 9.4（idat 批次 + IDAPython + Hex-Rays）對 `Bcan.exe` 完整反編譯。
> 以下位址均為 IDA VA（image base 0x140000000）。證據為反編譯後的 C 偽碼，
> 證據力高於字串層級。此節推翻/補完前文標「待查證」的項目。

### 4.1 CPU 時脈定案（推翻 MAME 流傳值）

- **主時基**：Bcan 以整數 `107386350`（= 2 × 53693175）作為「master tick」頻率
  （107.38635 MHz）。證據：
  - AVI 錄影寫檔器（func `0x14007B470`）計算
    `(1000000 × ticks + 53693175) / 107386350`，同時出現常數 `53693175`
    （0x3334AF7，即 U13 主晶振 53.693175 MHz）與 `107386350`（0x66695EE）。
  - master_tick 欄位（機器物件 +319016）在 fault report 中輸出。
- **68000 時脈 = 10.738635 MHz**（U13/5，即外界流傳值，**不是** MAME 的 /6）：
  主排程函式 `MachineSession::step`（vft[2]，func `0x14007F320`）的預算檢查為
  `10 × 68k_cycles`，即 **1 個 68k cycle = 10 個 master tick**
  （107.38635 MHz ÷ 10 = 10.738635 MHz，整除成立）。
- **65C02 時脈 = 3.579545 MHz**（流傳值）：107.38635 MHz ÷ 30 = 3.579545 MHz
  （3579545 × 30 = 107386350 整除成立）；音效取樣位置公式
  （$E90018 讀取，func `0x1400A23A0` case 0xA）使用常數
  `970772604000` = 3579545 × 271200 = 53693175 × 18080（多時脈 LCM 定點），
  旁證 UM6619 端確實以 3.579545 MHz 為基底。
- 結論：Bcan 的時脈模型與 MAME driver（/6、/12）**不同**，採用外界流傳的
  10.74/3.58 MHz。MAME 值應標為與 (a) 矛盾。記憶體映射文件已據此更新。

### 4.2 68k 位址匯流排實作（SystemBus 反編譯定案）

SystemBus vftable @ `0x140424CA0`；byte/word 讀寫四函式：
`0x1400A23A0`（byte read）、`0x1400A26A0`（word read）、
`0x1400A27F0`（byte write）、`0x1400A2C10`（word write），
下層位址分類器 `0x1400A3430`（產生 type+offset token 再分派）。
MAME `main_map` 的**所有區段 Bcan 都有實作**：

| 區段 | Bcan 實作細節（SystemBus 物件偏移） |
|---|---|
| `$000000–$3FFFFF` / `$F80000–$FBFFFF` | 卡帶 ROM（緩衝指標 +4112/+4120 = begin/end，越界讀回 0xFFFF）；overlay：低位 `$000000–$000FFF`（旗標 +300452）、高位 `$F80000–$F80FFF`（旗標 +300453），IPL 副本在物件 +16；卡帶存在旗標 +300451 |
| `$E80000–$E8FFFF` | 經函式指標（+300440）轉發 SoundHostPort 物件（byte 對調在該物件內） |
| `$E90000–$E9001F` | 音效主機埠：`$E90004/05`（+5168/+5169）、`$E9000C`（+5170）讀取閂；`$E90010` 讀寫（+300450 與 +168024 雙寫）；`$E90014/$E90016` = 16-bit DMA 位址暫存器（+168020/+168022）；`$E90018` = **DMA 取樣播放位置**（依模式即時計算，mode 4 用定點公式 `(t0 + rate×count)/970772604000`，clamp 到 $E90016 值）；`$E9000A` 觸發 SoundHostPort 虛函式 |
| `$E9001C/$E9001D` | 特殊型別（type 6/7）：`$E9001C` 寫入走 `sub_1400A3610`（overlay 控制，對應 IPL 關 overlay 動作） |
| `$E90020–$E9003F` | **2 通道 DMA**（ch0 +168072 / ch1 +168084，ch = (addr ≥ $E90030)），暫存器寫入 handler `sub_1400A31A0`，觸發後回呼 byte/word 讀寫函式搬資料 |
| `$E90B3C–$E90B3D` | NOP 區（type 8），與 MAME 一致 |
| `$EB0D00–$EB0D03` | UMC6650：偶位址寫入忽略；`$EB0D03` = 位址埠（寫 +300432，7-bit）；`$EB0D01` = 資料埠。**讀**：位址埠 $20–$2F → 讀 16 byte 金鑰（+300384，即 umc6650.bin）；$40–$5F → 讀內部 RAM（+300400）。**寫**：僅當（位址埠 & 0xE0)==0x40 才寫入內部 RAM——**金鑰區 $20–$2F 唯讀**。與 IPL 反組譯結論（bios-68k.md §3）一致，MAME `umc6650.cpp` 的埠角色確實寫反 |
| `$EC0000–$ECFFFF` | 卡帶 SRAM 32768 B（+135208），**僅奇位址有效**（index = addr>>1），寫入設 dirty 旗標 +300454 |
| `$F00000–$F001FF` | UM6618 暫存器窗（handler `sub_1400A8FA0` 寫 / `sub_1400A8DA0` 讀，物件 +168096） |
| `$F00200–$F003FF` | 調色盤 RAM 512 B（+168768） |
| `$F00400–$F3FFFF`、`$F60000–$F7FFFF` | **讀寫皆靜默 no-op**（open bus 不回 bus error） |
| `$F40000–$F5FFFF` | 68k 可見 VRAM 視窗 128 KiB（+169280），word 讀寫做 byte-swap（host 端 LE 儲存）；部分主機板物理裝片容量較大，見 hardware-implementation-sources.md |
| `$FC0000–$FFFFFF` | Work RAM 64 KB（+69672），offset = addr & 0xFFFF——**mirror 0x30000 實測成立**，且實際上 $FC–$FF 四個 64 KB 頁全映射同一 RAM |
| `≥ $1000000` | 回 type 2 錯誤（24-bit 位址外） |

- 匯流排錯誤碼（0=ok、2=寬度/位址錯、6/7/8/11/12/13=各區段違規）對應
  fault report 的 `bus_fault` 分類；越界 ROM 讀回 0xFFFF 而不丟 BusError。
- ROZ/scaling 屬於 UM6618 渲染器內部（render funcs `0x1400B1160` 等三個巨型函式，
  對應 8/4/2bpp 或三種模式），**非記憶體映射問題**；0.0.8b 自述未接完的是
  渲染效果，bus 層完整。

### 4.3 Save state（ACANRTS）二進位版面定案

寫入端 func `0x14006F8D0`、讀取/驗證端 func `0x14005E240`。檔案 =
96 byte 標頭 + payload（上限 < 16 MB）：

| Offset | 大小 | 內容 |
|---|---|---|
| 0x00 | 8 | magic `ACANRTS\0`（8 byte 比對 0x5354524E414341） |
| 0x08 | 2 | version = 1（讀端強制 ==1） |
| 0x0A | 2 | header size = 96（0x60，讀端強制 ==96） |
| 0x0C | 4 | 0（保留/flags） |
| 0x10 | 32 | 所屬 ROM 的 SHA-256（綁定遊戲） |
| 0x30 | 32 | 整體 SHA-256（寫入端對 header+payload 計算後回填；讀端驗證） |
| 0x50 | 8 | payload 大小（讀端檢查 == 檔案剩餘大小） |
| 0x60 | n | payload（機器快照，由背景執行緒產生） |

- 讀端比對 ROM SHA-256 不符即拒絕（「belongs to a different normalized ROM」）。
- payload 內部欄位順序由 snapshot 序列化器（`acan::state`，含
  ValidationAddressBus / ValidationW65C02Bus 兩個唯讀驗證代理匯流排）決定，
  **尚未逐欄位解析**（需再追 `sub_140096F50` 一系）。

### 4.4 Cheat 檔格式定案（.cht 為純文字）

寫入端 func `0x140089D00`、讀取端在 func `0x14004E080`。**`.cht` 不是二進位**，
是 tab 分隔文字檔：

```
; Bcan per-game cheat file
BCAN_CHT_1
<addr6hex>\t<value_dec>\t<value_hex 補零至 2×size 位>\t<1|0>\t<名稱>
```

- 位址為 6 位大寫 hex，儲存時已 OR 上 0xFC0000（cheat 只作用于 Work RAM）。
- value_hex 寬度依 size（1/2/4 byte → 2/4/8 位）；第 4 欄 1=啟用/鎖定 0=停用。
- 名稱中的控制字元（0x00/0x09/0x0A/0x0D）寫入前轉空格。
- 讀端接受兩個 magic：**`BCAN_CHT_1`（現行）與 `ACAN_CHTI` 開頭的舊版
  `ACAN_CHT_1`**（func `0x140052246` 同時比對 "ACAN_CHT"+"_1" 與
  "BCAN_CHT"+"_1"）——`ACAN_CHTI` 是早期/相容 magic，`BCAN_CHT_1` 為現行版本標記。
- 每遊戲 cheat 上限 1024 筆（`a4 >= 0x401` 拒絕）。

### 4.5 雙部分卡帶規則定案

- ZIP 須恰好含一個數字名 `.0` 部分 + 一個數字名 `.1` 部分
  （「A two-part cartridge ZIP must contain one numeric .0 part and one
  numeric .1 part.」）。
- 每部分有**固定大小與 CRC 驗證**（「ZIP extraction failed cartridge-part
  size or CRC verification」）。
- 已知配對（模擬器內建白名單）：**Super Light Saga = 16007.0（2 MiB）+
  08007.1（1 MiB）**；本 repo 的 Super Dragon Force ZIP（16007 (Taiwan).bin
  2 MB + 08002 (Taiwan).bin 1 MB）同屬此機制。映射方式：.0 為低位、.1 接續
  高位（合計 3 MiB 位於 $000000–$2FFFFF 視圖，無 mapper）。
- 未找到其他遊戲使用雙部分的證據。

### 4.6 其他發現

- MachineSession 物件在 +319016 維護 master_tick、+319080 為 frame 計數
  （snapshot 驗證函式 `0x1400812B0` 中有 ÷60 magic 0x8888888888888889，
  證實 60 Hz 顯示幀率基準）。
- 排程為 deadline 驅動：每個 68k timeslice 取最近事件（DMA、音效、
  畫面事件）為上限，事後做多欄位一致性檢查，不符即 stopped safely。
- 手把狀態在 68k 端由 `$E90004/05`、`$E9000C` 讀取（SystemBus +5168/+5170），
  配合 65C02 端 shift register（memory-map.md §5）—Bcan 兩側都有實作。
- 工作記憶體金手指寫入路徑會直接改 SystemBus 內的 Work RAM 副本
  （+69672），不做 bus 模擬。

## 5. 待查證

- `.rsrc` 中 616 KB 資源的實際內容（字型？UI 圖？）。
- ~~`BCAN_CHT_1` 與 `ACAN_CHTI` 的確切關係~~ → 已定案（§4.4）。
- save state payload（0x60 之後）的內部欄位版面（標頭已定案，§4.3）。
- ~~68k/65C02 時脈~~ → 已定案為 10.738635 / 3.579545 MHz（§4.1）。
- zh-TW 介面字串存放形式（UTF-16 字串表中未見中文，可能在資源段或
  壓縮存放）。
- 65C02 端的 ×30 master tick 倍率未在反編譯中直接目視到（由
  107386350/3579545=30 整除關係推定）；UM6619 暫存器層行為仍待補。
