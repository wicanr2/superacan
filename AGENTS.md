# Super A'Can 知識庫與重製基石

本專案的長期目標：**重製（remake）台灣自製 16 位元遊戲主機 Super A'Can 上的遊戲**。
本檔案是知識庫入口：收錄主機硬體/軟體規格、模擬器分析結果、後續研究方向。
所有結論須標註來源；未驗證的資訊一律標示「待查證」。

---

## 1. 主機簡介：Super A'Can

- **名稱**：Super A'Can（英文代號 **F-16**，中文名「敦煌」）
- **製造/發行**：敦煌科技（Funtech，聯華電子 UMC 子公司，主機失敗後解散）
- **類型**：第四世代 16 位元家用遊戲機
- **發售日**：1995-10-25（台灣）
- **定位**：硬體對標 Sega Mega Drive / Neo Geo 同世代主機；主機與手把外型模仿美版超級任天堂
- **遊戲**：全中文介面；已發售約 12 款（流通 ROM 約 8 款），另有約 11 款未發售
- **未實現計畫**：CD-ROM 與類似 Sega 32X 的硬體提升器，均未推出

來源：
- [Super A'Can - 維基百科（中文）](https://zh.wikipedia.org/wiki/Super_A%27Can)
- [Super A'Can - Wikipedia (en)](https://en.wikipedia.org/wiki/Super_A%27Can)
- [A'Can - 12bit.club](http://fuji.12bit.club/acan/)
- [經典技研堂：Super A'can 敦煌 - Cool3c](https://www.cool3c.com/article/123925)

## 2. 硬體規格

| 項目 | 規格 | 備註 |
|---|---|---|
| 主 CPU | Motorola 68000 @ **10.738635 MHz**（(a) Bcan 反編譯定案；MAME 用 U13/6≈8.95 MHz 為未定案猜測） | 與 MD/Neo Geo 同等級 |
| 副 CPU | WDC **65C02** @ **3.579545 MHz**（(a) 定案；早期資料誤記 MOS 6502） | 見 §4、docs/sound-driver.md |
| 主記憶體 | 64 KB Work RAM（另有 256 KB SRAM 一說，待查證） | 來源間不一致 |
| 副記憶體 | 32 KB | |
| VRAM | 128 KB | |
| DMA | 主機 DMA **2 通道**（(b) MAME 實作；外界流傳 8 組之說待查證） | 另有 UM6618 內部 sprite DMA |
| 繪圖晶片 | UMC **UM6618**（背景與動畫處理器） | 四層背景、精靈透明/縮放 |
| 音效晶片 | UMC **UM6619**（音樂與音訊處理、周邊） | |
| 色彩 | 32768 色中同時顯示 256 色 | |
| 解析度 | 320×240 為主（一說最高 640×480，待查證） | |
| 精靈 | 最大 256×256 像素 | |
| 其他晶片 | **UMC6650**（有 16 byte 的 BIOS dump，見 §4） | 功能待查證 |

> 注意：各來源規格互相矛盾處（RAM 容量、解析度、6502 vs 65C02）須以模擬器實作與 BIOS dump 為準逐一查證。

來源：
- [The Video Game Kraken - Super A'Can](https://videogamekraken.com/super-acan)
- [百度百科 A'can](https://baike.baidu.com/item/A'can/10125242)
- [Retro Console Museum - Super A'Can](https://retro.chiba.tw/en/consoles/super-a-can/)
- [GameTechWiki - Super A'Can](https://emulation.gametechwiki.com/index.php/Super_A%27Can)

## 3. 遊戲 ROM 清單（本 repo `Bcan008b/ROMS/`）

| 檔案 | 大小 | 遊戲 |
|---|---|---|
| Boom Zoo (Taiwan).bin | 512 KB | 轟炸動物園 |
| Formosa Duel (Taiwan).bin | 1 MB | 福爾摩沙大對決 |
| Journey to the Laugh (Taiwan).bin | 2 MB | 嘻遊記 |
| Monopoly - Adventure in Africa (Taiwan).bin | 1 MB | 大富翁：非洲冒險 |
| Sango Fighter (Taiwan).bin | 3 MB | 三國志武將爭霸 |
| Speedy Dragon (Taiwan).bin | 2 MB | 音速飛龍 |
| Super Dragon Force (Taiwan).zip | 2 MB（壓縮） | 超級龍虎霸 |
| Super Taiwanese Baseball League (Taiwan).bin | 2 MB | 超級台灣職棒聯盟 |
| The Son of Evil (Taiwan).bin | 2 MB | 惡魔之子 |

- 中文遊戲名稱對照為**待查證**項目，須以實際 ROM header / 遊戲畫面確認。
- ROM 格式：raw binary（`.bin`），無 iNES 式標頭（待分析確認）。

## 4. 模擬器分析：Bcan 0.0.8b（`Bcan008b/`）

### 4.1 基本資訊
- `Bcan.exe`：PE32+ Windows x86-64 GUI 程式（約 5.4 MB），內嵌版本字串 `bcan_version=0.0.8b`
- `Bcan.ini`：portable 設定檔（`version=1`，未知 key 向前向後相容忽略）
- 介面語言預設 `zh-TW`；支援 mp4 錄影、即時存檔（save state）、截圖、crt 濾鏡、整數縮放

### 4.2 CPU 模擬核心（`THIRD_PARTY_NOTICES.txt`）
- **Moira**：Motorola 68k 模擬核心（MIT，Dirk W. Hoffmann）→ 主 CPU
- **CLK 65C02**：WDC 65C02 核心（MIT，Thomas Harte）→ 副 CPU 實為 65C02 而非原版 6502
- 其他：RAD Game Tools / Rich Geldreich（壓縮相關）、Angelo Salese / Ryan Holtz / superctr（MAME 相關程式碼，可能含音效/視訊實作）

### 4.3 BIOS 檔案（`bios/`）
- `supracan.zip`（TorrentZip）：
  - `internal_68k.bin`（4 KB）— 68k 內部 ROM（IPL/boot）
  - `internal_6502_1.bin`、`internal_6502_2.bin`（各 8 KB）— 65C02 端韌體
- `umc6650.zip`：`umc6650.bin`（**僅 16 bytes**）— UMC6650 晶片資料，推測為小型 PLD/狀態表

### 4.4 輸入配置（`Bcan.ini`）
- 手把按鍵：方向 + Start/Select + A/B/C/X/Y/Z **六鍵**（類似 MD 六鍵手把）
- 手把按鍵 bitmask 值（1,2,4,8,16,32,256,512,4096,8192,16384,32768）透露模擬器內部按鍵編碼順序
- 雙人支援（p1/p2）

### 4.5 待分析項目
- [x] 逆向 `Bcan.exe` 的記憶體映射（68000 / 65C02 位址空間、UM6618/UM6619 暫存器位址）→ [docs/memory-map.md](docs/memory-map.md)（68k 空間以 MAME driver (b) 為骨架，Work RAM `$FC0000–$FCFFFF`、卡帶 SRAM 32768 B 經 Bcan (a) 確認；65C02 端 I/O `$0400–$04FF`）
- [x] 比對 MAME `supracan.cpp` driver 實作差異 → 確認 Bcan 硬體層移植自 MAME driver（內嵌 BSD-3-Clause / Angelo Salese、Ryan Holtz 授權字串 (a)）；BIOS 三檔 SHA-1 與 MAME 記載一致
- [x] BIOS 三個 bin 的反組譯（68k IPL 流程、65C02 音訊通訊協定）→ [docs/bios-68k.md](docs/bios-68k.md)、[docs/bios-65c02.md](docs/bios-65c02.md)。結論：68k IPL = UMC6650 交握 + 卡帶 `$2000` 授權資料比對（類 TMSS，含 `(reverse engineer)` 彩蛋）+ 跳卡帶向量入口；兩塊「6502 bin」其實是**取樣資料**（複製進 sound RAM `$0000–$3FFF`），65C02 程式由卡帶上傳。後續：反組譯遊戲上傳的 65C02 音效驅動才能補完音訊協定細節
- [x] ROM header 格式與 bank 切換（mapper）機制 → 無外加標頭、16-bit word-swap 向量表格式、無 mapper；入口點已驗證為合法 68k 程式碼（[docs/bios-rom-format.md](docs/bios-rom-format.md)）
- [x] 存檔（save state）格式 → magic `ACANRTS`、10 槽位、96-byte 標頭（version/headersize/ROM SHA-256/整體 SHA-256/payload 大小），payload 欄位版面待查；cheat 檔實為 **tab 分隔純文字**（標頭 `BCAN_CHT_1`，相容舊 magic `ACAN_CHT_1`）（[docs/emulator-analysis.md](docs/emulator-analysis.md) §4）
- [x] 遊戲 65C02 音效驅動反組譯 → [docs/sound-driver.md](docs/sound-driver.md)。結論：68k 把命令串寫到 sound RAM `$0300`、寫 `$E9000A` 觸發 65C02 IRQ bit5；6 條命令（UM6619 raw 寫/啟停通道/取樣播放等），ack=`$0300=$FF`；手把由 65C02 掃描放 `$0200/$0202`；取樣 = 68k DMA 入 sound RAM + IRQ6 雙緩衝串流；UM6619 為 PCM/取樣式合成（無 FM 跡象）。Speedy Dragon 另有第二套音樂驅動、Boom Zoo 用壓縮上傳（自訂 Huffman/RLE）
- [x] CPU 時脈定案 → Bcan 反編譯：master tick 107.38635 MHz，68k=10.738635 MHz、65C02=3.579545 MHz（流傳值成立，推翻 MAME /6 /12 猜測）（[docs/memory-map.md](docs/memory-map.md) §1、[docs/emulator-analysis.md](docs/emulator-analysis.md) §4.1）

### 4.6 模擬器機制（逆向確認，(a) 級）

> 細節見 [docs/emulator-analysis.md](docs/emulator-analysis.md)。

- **架構**：原生 Win32 x86-64 + Direct3D 11；C++ 命名空間 `acan::{cpu,core,hardware,session,state}`；68k 用 Moira、副 CPU 用 CLK 65C02、硬體層移植自 MAME `supracan.cpp`（授權字串佐證）
- **BIOS**：`bios/supracan.zip` + `umc6650.zip` 必備，逐成員驗證檔名/大小/CRC；68k IPL 載入時做 reset-vector 正規化（word-swap）；冷開機有步數上限，BIOS 須在限期內跳到卡帶入口。IPL 反組譯（[docs/bios-68k.md](docs/bios-68k.md)）：UMC6650 交握（`$EB0D03`=位址埠、`$EB0D01`=資料埠）→ 卡帶 `$2000` 授權比對 → 設 `$E9001C` bit1/bit3 關 overlay → 跳卡帶向量入口；兩塊 6502 bin 為取樣資料（[docs/bios-65c02.md](docs/bios-65c02.md)）
- **ROM**：只收 `.bin` raw image 與 bounded `.zip`；支援雙部分卡帶（數字 `.0`/`.1`，如 Super Light Saga = 2 MiB + 1 MiB）；ROM 以 SHA-256 作為 game identifier
- **時脈模型**：master tick 107.38635 MHz（2×U13）；68k ×10、65C02 ×30（emulator-analysis.md §4.1）
- **匯流排**：SystemBus 讀寫分派全區段已反編譯確認（含 SRAM 僅奇位址、no-op 區段、Work RAM addr&0xFFFF 映射、越界 ROM 讀回 0xFFFF）；UMC6650 金鑰區 `$20–$2F` 唯讀，確認 MAME `umc6650.cpp` 埠角色寫反
- **Work RAM**：`$FC0000–$FCFFFF`（64 KiB）——cheat 搜尋範圍字串直接證實
- **Save state**：magic `ACANRTS`、槽位 0–9、96-byte 標頭＋payload、指令邊界擷取、背景寫入、transactional restore（失敗 rollback）
- **Cheat**：內建 RAM 搜尋/金手指管理器；`.cht` 為 tab 分隔純文字（標頭 `BCAN_CHT_1`、上限 1024 筆、相容舊 magic `ACAN_CHT_1`），cheat 寫入直改 Work RAM 副本不走 bus
- **卡帶存檔**：固定 32768 byte SRAM 映像，背景 worker 寫入
- **錄影/截圖**：MP4（MF H.264/AAC）或 AVI（MJPEG，1.75 GB 上限）；PNG 截圖至 `snap\`
- **安全設計**：所有邊界/未知硬體操作「stopped safely」，輸出 `*.fault.txt` 自動故障報告（含 pc/opcode/各 fault 計數）
- **音效協定**：68k→65C02 命令 mailbox（sound RAM `$0300` 命令串 + `$E9000A` 觸發 IRQ bit5）、UM6619 PCM/取樣合成、取樣 DMA 雙緩衝 → [docs/sound-driver.md](docs/sound-driver.md)
- **分析工具**：本機 IDA Pro 9.4（`Bcan008b/Bcan.exe.i64` 已建置，48 MB IDB 留供後續；注意授權不含 68k/65C02 處理器模組，反組譯遊戲碼用 Capstone）
- **自述完成度**：0.0.8b 仍有 ROZ/scaling/mixing 效果未接完（狀態列 test build 字串）

## 5. 參考資源

- MAME Super A'Can driver（本文件對照時 master 路徑為 `src/mame/umc/supracan.cpp`，曾用 `src/mame/funtech/supracan.cpp`（現已 404）/ `src/mame/misc/supracan.cpp`，Angelo Salese 等）— 最權威的硬體文件替代品
- [GameTechWiki Super A'Can](https://emulation.gametechwiki.com/index.php/Super_A%27Can) — 模擬支援現況
- [12bit.club A'Can 站](http://fuji.12bit.club/acan/) — 遊戲截圖與硬體筆記

### 5.1 GitHub 相關專案（2026-08-30 調查）

- [splash5/superacan-notes](https://github.com/splash5/superacan-notes) — 硬體研究筆記（PCB 照片、電路圖、手把 SNES 協定轉接、UMC6650 分析；其 6650 協定結論與本知識庫 IPL 反組譯一致，可互相佐證）
- [anomixer/superacan-web](https://github.com/anomixer/superacan-web) — MAME 核心的 WebAssembly 線上模擬器（12 款遊戲全支援）；有針對 UM6619 DMA 握手的音效修正（sndfix 核心），對 Linux 重製的音訊實作有參考價值
- MAME 本體（`mamedev/mame`）— Linux 上目前唯一可跑 Super A'Can 的選項（音效 preliminary）
- 調查結論：**GitHub 上沒有 Bcan 的原始碼或 Linux 移植**；Bcan 為閉源 Windows 程式，Linux 重製須以本知識庫 + MAME driver（BSD-3-Clause）為基礎自行實作

### 5.2 分析工具（本 repo `tools/`）

- `tools/deswap.py` — ROM/BIOS 16-bit word-swap 轉換（雙向對稱）
- `tools/rominfo.py` — 顯示 ROM 大小/SHA-256/向量表 SSP/PC/`$2000` 授權區
- 臨時 IDAPython 探針腳本在 `/tmp/ida_acan/`（未入庫，重開機即失；需要時可依 docs/ 重建）

## 6. GitHub Repo 規劃

| Repo 名稱 | 用途 | 狀態 |
|---|---|---|
| `superacan` | 硬體/軟體規格、逆向分析文件（`docs/`）＋ ROM/BIOS 分析與萃取工具（`tools/`） | 規劃中 |

- 目前只建立一個 repo（docs + tools 合併，即本目錄）。遊戲 remake 專案**暫不建立**，等確定要重製哪款遊戲後再開新 repo（命名屆時依遊戲決定，例如 `superacan-remake-<game>`）。
- **Linux 模擬器重製**：repo 已建立於本機 `../superacan-emu/`（尚未上 GitHub；建議名 `superacan-emu`），目標是在 Linux 上重製 Bcan 的模擬能力。Bcan 為閉源 Windows 程式、GitHub 上無移植（§5.1）；實作基礎為本知識庫（(a) 級記憶體映射/時脈/音訊協定）＋ MAME driver（BSD-3-Clause，可直接取用）＋ Moira（68k）/CLK（65C02）核心（皆 MIT）。
  - **里程碑 1 完成（2026-08-31）**：SystemBus 全表＋UMC6650＋Moira 68k，IPL 跑通 lockout/授權檢查並跳入卡帶入口（Boom Zoo `$412`、Monopoly `$24C6`，與知識庫交叉驗證一致；驗證 log 見 superacan-emu/docs/verify-ipl.md）。後續：UM6618 繪圖、65C02/UM6619 音效、SDL2 視窗。
  - **里程碑 2 完成（2026-08-31）**：UM6618（3 tilemap＋sprite＋window 0＋sprite DMA；ROZ stub）、主機 DMA 2 通道、vblank/raster/line IRQ（IRQ7/4/5，HOLD_LINE 語意）、65C02 實跑（命令 mailbox/boot ack/重新上傳）、SDL2 視窗。Boom Zoo、Monopoly、Speedy Dragon 畫面驗證通過（截圖與細節見 superacan-emu/docs/verify-video.md）。**新發現**：
    - `$E9001C` bit1/bit3 的 IPL overlay 關閉是**單向 latch**（遊戲上傳音效驅動時會把整個暫存器清 0；若 overlay 隨之恢復，卡帶中斷向量會被 IPL 的 `rte` 表蓋回，主迴圈停擺）——修正 §4.6「BIOS」節語意。
    - 68k IRQ 需 HOLD_LINE 語意（CPU ack 後解除），否則用 `STOP #$2700` 等 vblank 的遊戲會鎖死在中斷再進入循環。
    - Speedy Dragon 第二音效驅動的 DMA control 實測為 `$B800`（word 模式），sound-driver.md §1.2 的 `$2648` 應修正；第二驅動後續命令協定仍待查證（IRQ enable 切成 `$0C` 後 68k 端停在 `$28DE` 等待）。
  - 實測佐證：IPL 轉交點 `JMP $F80604`（高區視圖）在模擬器實跑中確認，與 docs/bios-68k.md §2 一致。
  - **里程碑 3+4 完成（2026-08-31）**：UM6619 PCM 音效合成（16 通道、period/音量/key/DMA 雙緩衝/timer IRQ，原生 44744 Hz→48 kHz 線性插值；演算法依 MAME `umc6619_sound.cpp` BSD-3-Clause 重新實作）、SDL2 音訊輸出＋headless `--wav` 錄音、手把輸入（SDL 鍵盤＋headless `--press` 注入；shift register 與 direct mode 兩路皆通）。Boom Zoo/Monopoly 音樂＋按鍵反應（標題按 Start 進入選擇畫面）驗證通過（數據見 superacan-emu/docs/verify-audio-input.md）。**Speedy Dragon 第二音樂驅動已修復**（里程碑 2 的已知缺陷），根因三層：
    - CLK 6502Mk2 的 Reset 是 level-triggered 且只在給 cycle 時捕捉——HALT 期間不給 cycle 會讓 reset「設了又清」整個消失；手動補跑固定 7-cycle 又會截斷序列。正確做法：釋放後**繼續拉住 Reset 線**直到 CPU 進入 reset 序列（讀 `$FFFC` 向量）再放開。
    - **65C02 IRQ 來源是 level-held、各有專屬 ack**（bit2←讀 `$0405`、bit3←讀 `$0404`、bit5←讀 `$040A`、bit6←讀 UM6619 reg `$16`、bit7←讀 reg `$14`），`$0411` 是純狀態暫存器——MAME 的「讀取即清全部」會丟同時發生的來源（(a) 級修正，memory-map.md §5 已更新）。
    - latch `$0404/$0405` 空讀回 `$CD`，68k 經 `$E80404/05` 窗口寫入觸發 IRQ；開機 probe 靠 `$0407` 清除脈衝觸發 latch IRQ 讀到 `$CD` 快速結束（觸發條件為功能推測）。
    - 第二驅動結構反組譯完成（sound-driver.md §2.2）；實際上傳常式為 68k `$34E4`（control `$B800`），靜態碼 `$954`（`$2648`）無呼叫者。
- 版權隔離：ROM/BIOS 等受版權保護檔案**不上傳** GitHub，repo 的 `.gitignore` 預設排除 `*.bin`、`Bcan008b/` 整個目錄（含 ROM 與模擬器執行檔）。

## 7. 工作守則

1. **事實分級**：所有規格須標明來源層級 —（a）模擬器實作/BIOS dump 實測 >（b）MAME driver >（c）維基/媒體報導。矛盾時以 (a) 為準並記錄差異。
2. **不猜測**：查不到的硬體細節寫「待查證」，不要憑類似主機（MD/SFC）的經驗填入。
3. **分析產出**：對 `Bcan008b/` 的任何逆向/分析結果，以 Markdown 寫入 `docs/`（例如 `docs/memory-map.md`、`docs/bios-68k.md`），並在本檔案 §4.5 勾選對應項目。
4. **版權注意**：ROM 與 BIOS 為受版權保護內容，分析可，但不要將其內容大段複製進文件或重製素材；remake 的美術/音樂須重新創作。
5. **最小變更**：文件與工具腳本保持簡單，能回答問題即可，不做過度工程。
