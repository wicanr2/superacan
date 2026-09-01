# Super A'Can 知識庫與重製基石

本專案的長期目標：**重製（remake）台灣自製 16 位元遊戲主機 Super A'Can 上的遊戲**。
本檔案是知識庫入口：收錄主機硬體/軟體規格、模擬器分析結果、後續研究方向。
所有結論須標註來源；未驗證的資訊一律標示「待查證」。

## 0. 專案入口與目前真相

- 面向讀者的穩定入口為 [`README.md`](README.md)；本檔保存 agent 作業規則、研究現況與
  證據分級，不把逐輪命令或失敗嘗試累積到 README。
- 工作歷程唯一寫入 [`WORKLOG.md`](WORKLOG.md)；逆向證據仍寫入 `docs/` 的對應主題文件。
- 硬體架構摘要為 [`assets/hardware/super-acan-hardware.svg`](assets/hardware/super-acan-hardware.svg)，
  但 SVG 只供導覽，不取代文件中的原始位址、bytes、工具版本與推論等級。
- 實機照片及其作者、授權、來源與雜湊統一記錄於
  [`assets/hardware/README.md`](assets/hardware/README.md)。只有授權明確的圖片可納入 Git；
  來源不明、拍賣站或一般媒體照片只能外部連結，不得因「歷史照片」需求直接下載重發。
- `Bcan008b/`、ROM、BIOS、Bcan 執行檔與 `.i64` 是本機研究輸入，不是公開交付物；
  不得加入 Git、GitHub Release 或任何公開 `dist-all/`。

---

## 1. 主機簡介：Super A'Can

- **名稱**：Super A'Can（英文代號 **F-16**，中文名「敦煌」）
- **製造/發行**：敦煌科技（Funtech，聯華電子 UMC 子公司，主機失敗後解散）
- **類型**：第四世代 16 位元家用遊戲機
- **發售日**：1995-10-25（台灣）
- **定位**：硬體對標 Sega Mega Drive / Neo Geo 同世代主機；主機與手把外型模仿美版超級任天堂
- **遊戲**：MAME 固定 catalog 列 F001–F012 共 12 款正式遊戲，並註明已知正式遊戲皆已 dump；
  本地有其中 9 款。該 catalog 另列 4 個未發售名稱，不把其他來源的「約 11 款」當定案
- **未實現計畫**：CD-ROM 與類似 Sega 32X 的硬體提升器，均未推出

來源：
- [Super A'Can - 維基百科（中文）](https://zh.wikipedia.org/wiki/Super_A%27Can)
- [Super A'Can - Wikipedia (en)](https://en.wikipedia.org/wiki/Super_A%27Can)
- [A'Can - 12bit.club](http://fuji.12bit.club/acan/)
- [經典技研堂：Super A'can 敦煌 - Cool3c](https://www.cool3c.com/article/123925)

## 2. 硬體規格

| 項目 | 規格 | 備註 |
|---|---|---|
| 主 CPU | Motorola **MC68HC000P10** @ **10.738635 MHz**（型號為 (p) 板級證據；時脈為 (a) Bcan 反編譯定案；MAME 用 U13/6≈8.95 MHz 為未定案猜測） | 68000 相容、低功耗 CMOS 型號 |
| 副 CPU | WDC **65C02** @ **3.579545 MHz**（(a) 定案；早期資料誤記 MOS 6502） | 見 §4、docs/sound-driver.md |
| 主記憶體 | 64 KiB Work RAM | 2×32K×8 板級證據 (p)＋Bcan `$FC0000–$FCFFFF` (a)；舊網頁 256 KiB 說法不採用 |
| 副記憶體 | 實體 32 KB（單顆 `UM62256`, (p)）；65C02 位址空間與 68k `$E80000` 視窗皆 64 KB，上半疑為 alias、**待查證** | 見 docs/memory-map.md §5.1 |
| VRAM | 68k 可見視窗 128 KiB；`PCGAM 16000-2A` 板為 2×`UM611024`，物理合計 256 KiB；UM6618 `VRAM_A17` 接 SRAM `A16`，上半部 consumer 待查證 | 較早板級筆記為 2×`UM61512`、合計 128 KiB，可能有 revision 差異；見 docs/vram-architecture.md |
| DMA | 主機 DMA **2 通道**（(b) MAME 實作；外界流傳 8 組之說待查證） | 另有 UM6618 內部 sprite DMA |
| 繪圖晶片 | UMC **UM6618**（背景與動畫處理器） | 四層背景、精靈透明/縮放 |
| 音效晶片 | UMC **UM6619**（音樂與音訊處理、周邊） | |
| 色彩 | 32768 色中同時顯示 256 色 | |
| 解析度 | 256/320 水平模式；224/240 可視高度（register observation）；常用輸出 320×240 | 未找到 640×480 的 register／實作證據，不列為已知模式 |
| 精靈 | 最大 256×256 像素 | |
| 其他晶片 | **UMC6650**（16-byte key dump） | lockout 開機流程已確認；只剩 `$09/$0C` 外部 pin 語意待查證 |

> 注意：各來源規格互相矛盾處（RAM 容量、解析度、6502 vs 65C02）須以模擬器實作與 BIOS dump 為準逐一查證。

來源：
- [The Video Game Kraken - Super A'Can](https://videogamekraken.com/super-acan)
- [百度百科 A'can](https://baike.baidu.com/item/A'can/10125242)
- [Retro Console Museum - Super A'Can](https://retro.chiba.tw/en/consoles/super-a-can/)
- [GameTechWiki - Super A'Can](https://emulation.gametechwiki.com/index.php/Super_A%27Can)

## 3. 遊戲 ROM 清單（本 repo `Bcan008b/ROMS/`）

| 檔案 | 大小 | 遊戲 |
|---|---|---|
| Boom Zoo (Taiwan).bin | 512 KB | 爆爆動物園（F011） |
| Formosa Duel (Taiwan).bin | 1 MB | 福爾摩沙大對決 |
| Journey to the Laugh (Taiwan).bin | 2 MB | 嘻遊記 |
| Monopoly - Adventure in Africa (Taiwan).bin | 1 MB | 非洲探險（F008） |
| Sango Fighter (Taiwan).bin | 3 MB | 三國志 武將爭霸（F002） |
| Speedy Dragon (Taiwan).bin | 2 MB | 音速飛龍 |
| Super Dragon Force (Taiwan).zip | 3 MiB 內容 | **超級光明戰史（F007）**；ZIP／成員檔名誤標，hash 已定案 |
| Super Taiwanese Baseball League (Taiwan).bin | 2 MB | 超級中華職棒聯盟（F005） |
| The Son of Evil (Taiwan).bin | 2 MB | 邪惡之子（F003） |

- 完整 F001–F012 catalog、發行商、年份、CRC／SHA 與本地對照見
  [docs/software-catalog.md](docs/software-catalog.md)。
- ROM 格式已確認為 raw binary、無模擬器外加標頭、16-bit word-swap。

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
  - `internal_6502_1.bin`、`internal_6502_2.bin`（各 8 KB）— 開機載入 sound RAM 的內建取樣資料，**不是 65C02 韌體**
- `umc6650.zip`：`umc6650.bin`（**僅 16 bytes**）— UMC6650 `$20–$2F` 唯讀金鑰，不是 PLD 熔絲圖
- 四個成員的 CRC32、SHA-1、SHA-256 與兩個本機 ZIP 容器 SHA-256 見
  [docs/bios-rom-format.md](docs/bios-rom-format.md) §1；功能型模擬所需成員完整，但 dump provenance／revision 未知

### 4.4 輸入配置（`Bcan.ini`）
- 手把按鍵：方向 + Start/Select + A/B/C/X/Y/Z **六鍵**（類似 MD 六鍵手把）
- 手把按鍵 bitmask 值（1,2,4,8,16,32,256,512,4096,8192,16384,32768）透露模擬器內部按鍵編碼順序
- 雙人支援（p1/p2）

### 4.5 分析項目與剩餘缺口
- [x] 逆向 `Bcan.exe` 的記憶體映射（68000 / 65C02 位址空間、UM6618/UM6619 暫存器位址）→ [docs/memory-map.md](docs/memory-map.md)（68k 空間以 MAME driver (b) 為骨架，Work RAM `$FC0000–$FCFFFF`、卡帶 SRAM 32768 B 經 Bcan (a) 確認；65C02 端 I/O `$0400–$04FF`）
- [x] 比對 MAME `supracan.cpp` driver 實作差異 → 確認 Bcan 硬體層移植自 MAME driver（內嵌 BSD-3-Clause / Angelo Salese、Ryan Holtz 授權字串 (a)）；BIOS 四個成員的 CRC32／SHA-1 與 MAME 記載一致
- [x] BIOS 三個 bin 的反組譯（68k IPL 流程、65C02 端資料用途與開機流程）→ [docs/bios-68k.md](docs/bios-68k.md)、[docs/bios-65c02.md](docs/bios-65c02.md)。結論：68k IPL = UMC6650 交握 + 卡帶 `$2000` 授權資料比對（類 TMSS，含 `(reverse engineer)` 彩蛋）+ 跳卡帶向量入口；兩塊「6502 bin」其實是**取樣資料**（複製進 sound RAM `$0000–$3FFF`），65C02 程式由卡帶上傳；遊戲驅動與通訊協定已另於 [docs/sound-driver.md](docs/sound-driver.md) 完成主要資料流分析
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
- **匯流排**：SystemBus 讀寫分派全區段已反編譯確認（含 SRAM 僅奇位址、no-op 區段、Work RAM addr&0xFFFF 映射、越界 ROM 讀回 0xFFFF）；UMC6650 金鑰區 `$20–$2F` 唯讀，埠角色與 IPL／MAME device 一致
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
- [硬體組成與逐晶片模擬實作參考](docs/hardware-implementation-sources.md) — 固定來源 commit、PCB revision 差異、各晶片可參考核心與不可照抄的已知缺口
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
| `superacan` | 硬體/軟體規格、逆向分析文件（`docs/`）＋ ROM/BIOS 分析與萃取工具（`tools/`） | 本機 Git repo；尚未建立 GitHub repo |

- 目前只建立一個 repo（docs + tools 合併，即本目錄）。遊戲 remake 專案**暫不建立**，等確定要重製哪款遊戲後再開新 repo（命名屆時依遊戲決定，例如 `superacan-remake-<game>`）。
- **Linux 模擬器重製**：repo 已建立於本機 `../superacan-emu/`（尚未上 GitHub；建議名 `superacan-emu`），目標是在 Linux 上重製 Bcan 的模擬能力。Bcan 為閉源 Windows 程式、GitHub 上無移植（§5.1）；實作基礎為本知識庫（(a) 級記憶體映射/時脈/音訊協定）＋ MAME driver（BSD-3-Clause，可閱讀與重新實作）；CPU 核心已改為獨立實作，Moira／CLK 只作差分 oracle。
  - 該 repo 的里程碑進度、驗證數據與截圖由它自己的 `WORKLOG.md` 與 `docs/verify-*.md` 保存，本庫不轉錄；以下只列已回饋到本庫並寫入對應文件的硬體結論。
  - `$E9001C` bit1/bit3 的 IPL overlay 關閉是**單向 latch**：遊戲之後把整個暫存器清 0 不得恢復 overlay，否則卡帶中斷向量會被 IPL 的 `rte` 表蓋回（docs/bios-68k.md、docs/chip-emulation-guide.md §2）。
  - 68k IRQ 採 **HOLD_LINE** 語意，CPU 受理該 level 後才解除來源；否則用 `STOP #$2700` 等 vblank 的遊戲會鎖死（docs/memory-map.md §6）。
  - 65C02 六個 IRQ 來源為 **level-held 且各有專屬 ack**，`$0411` 只是狀態暫存器（docs/memory-map.md §5、docs/sound-driver.md §3）。
  - 65C02 釋放 HALT 後必須維持 Reset 線直到 CPU 讀 `$FFFC`，否則 reset 序列被截斷（docs/chip-emulation-guide.md §3.1）。
  - latch `$0404/$0405` 空讀回 `$CD`，68k 經 `$E80404/05` 窗口寫入觸發對應 IRQ（docs/sound-driver.md §3、§4.3）。
  - Speedy Dragon 第二音樂驅動的實際上傳常式是 68k `$34E4`、DMA control `$B800`；靜態碼 `$954`（`$2648`）無呼叫者（docs/sound-driver.md §1.2、§2.2）。
  - IPL 轉交點 `JMP $F80604`（高區視圖）已由實跑確認，與 docs/bios-68k.md §2 一致。
- 版權隔離：ROM/BIOS 等受版權保護檔案**不上傳** GitHub，repo 的 `.gitignore` 預設排除 `*.bin`、`Bcan008b/` 整個目錄（含 ROM 與模擬器執行檔）。

## 7. 工作守則

1. **事實分級**：所有規格須標明來源層級 —（a）模擬器實作/BIOS dump 實測 >（b）MAME driver >（c）維基/媒體報導。另以（p）表示實機照片、晶片絲印、PCB 走線或板級電路圖；(p) 可證明物理裝片與接線，不能單獨證明暫存器行為。行為矛盾時以 (a) 為準並記錄差異。
2. **不猜測**：查不到的硬體細節寫「待查證」，不要憑類似主機（MD/SFC）的經驗填入。
3. **分析產出**：對 `Bcan008b/` 的任何逆向/分析結果，以 Markdown 寫入 `docs/`（例如 `docs/memory-map.md`、`docs/bios-68k.md`），並在本檔案 §4.5 勾選對應項目。
4. **版權注意**：ROM 與 BIOS 為受版權保護內容，分析可，但不要將其內容大段複製進文件或重製素材；remake 的美術/音樂須重新創作。
5. **最小變更**：文件與工具腳本保持簡單，能回答問題即可，不做過度工程。
6. **README 職責**：README 只放專案用途、現況摘要、穩定文件入口、合法素材邊界與
   可重現工具用法；日期 checkpoint、完整命令、失敗分類及 commit 流水帳寫入 `WORKLOG.md`。
7. **視覺證據**：硬體照片、原版畫面與示意圖必須分開標示。照片須記錄作者、來源頁、
   授權與本機 SHA-256；示意 SVG 必須標明其證據層級及不確定部分，不能冒充原廠線路圖。
8. **歷史照片**：「實機照片」與「當年拍攝的照片」不是同一件事。只有來源頁能證明拍攝
   年代時才能宣稱為當年照片；否則應寫成「後來拍攝的 1995 年實機」。
