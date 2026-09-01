# 工作歷程

## 2026-09-01：知識庫正確性稽核與外部來源複查

- 目標：逐項複驗 `docs/` 的斷言與證據等級，找出互相矛盾與過期結論，並用外部原始碼／
  schematic 補足缺口。
- 本機重驗（Docker、唯讀掛載）：四個 BIOS 成員與兩個 ZIP 容器的 CRC32／SHA-1／SHA-256、
  九款本地 ROM 的雜湊與向量表、`$F001F0` 立即寫入點、`$E8xxxx` 與 `$E900xx` 的 ROM 引用
  分布，全部重算。
- 訂正：Formosa Duel 入口 PC 由 `$00000426` 改為實測的 `$00002416`；撤除六處
  「MAME `umc6650.cpp` 埠角色寫反」的斷言（該斷言把 bus 位址當成 device offset，
  MAME 的 offset = 位址>>1，三方其實一致）；對齊 `bios-65c02.md` 的 sound RAM 位元組序
  與 `emulator-analysis.md` §4.6 的 `$E90004/05`／`$E9000C` 角色。
- 新增：`memory-map.md` §2.1（UM6619 主機端埠逐暫存器，MAME 與 Bcan 兩套解讀並列，
  含 `$E90010` IRQ mask、`$E90014/16` FRC 與 DMA 位址之爭、`$E90018` 的兩種讀值語意）、
  §5.1（sound RAM 實體 32 KiB 與 64 KiB 位址空間的落差與 alias 推論）；UM6618 `$0A`／`$0C`
  raster 觸發列；65C02 NMI 來源；手把對應的 SNES 轉接佐證；`internal_68k.bin` 可能位於
  UM6619 的線索；F003 A/B 實驗前需先固定 visible area 的提醒。
- 外部來源：以 Docker 內建網路抓取 MAME master 與固定 commit `6ae579a` 的
  `supracan.cpp`／`umc6650.cpp`／`umc6619_sound.cpp` 逐 byte 比對，兩者相同；
  `superacan-notes` 仍為 `63731a2`、`angelosa/hw_docs` 仍為 `1b9e8fe`；Bcan 公開版本
  仍是 0.0.8b。逐 net 解析 `APU.sch` 確認 sound RAM 只接 `A0..A14`。
- 文風：撤掉 `sound-driver.md` §0、`emulator-analysis.md` §5、`sound-driver.md` §3／§4.3 的
  修正過程自述；`AGENTS.md` §6 的 superacan-emu 里程碑流水帳改為「已回饋的硬體結論」清單。
- 未完成：sound RAM 上半區是否真為 alias、`$E90014/16` 兩套解讀的定案、F003 pixel-mode
  bit 3 的同狀態 A/B，都需要動態 trace 或實機量測。

## 2026-08-31：專案入口、硬體圖與實機照片

- 目標：review 現有知識庫，建立穩定 README，補充硬體 SVG 與可合法納入的實機照片。
- 變更：新增 `README.md`、硬體架構 SVG、圖片來源與授權台帳；更新 `AGENTS.md` 的入口與素材規則。
- 一致性勘誤：`docs/bios-65c02.md` 的早期「通訊待遊戲碼驗證」與 4.47 MHz 猜測已被
  後續遊戲驅動分析及 Bcan 反編譯推翻；更新現況並連回固定證據入口，保留訂正理由。
- 素材：採用 Evan-Amos 釋出至公有領域的 Wikimedia Commons 主機全套與主機板照片；
  未採用拍賣網站、媒體文章及來源不明圖片。
- 驗證：兩張 JPEG 已人工檢視並以 ImageMagick 確認格式／尺寸；SVG 通過 XML 解析並以
  headless Chrome 實際渲染檢視；本機 Markdown 連結、UID/GID、Git 差異與 Docker 清理均通過。
- 未完成：若未來找到具明確授權的 1995 年當年新聞／展場照片，再依同一台帳審查納入。

## 2026-08-31：網路硬體資料與模擬實作來源複查

- 目標：再次查找 Super A'Can 板級資料，補齊主要元件、revision 差異及逐晶片模擬參考。
- 固定來源：MAME `6ae579a`、`splash5/superacan-notes` `63731a2`、
  `anomixer/superacan-web` `929e51c`，並交叉查核 WDC／Motorola／Samsung 資料表及
  Emmanuel Vadot 板級筆記。
- 主要訂正：CPU 絲印細化為 `MC68HC000P10`；VRAM 改為「68k 視窗 128 KiB」，並
  記錄早期 128 KiB 裝片與 `16000-2A` 256 KiB 裝片的 revision／bank 未知。
- 新增：`docs/hardware-implementation-sources.md`，列出 UM6618、UM6619、UM6650、
  CPU、卡帶、palette、NTSC encoder 與手把的參考實作和已知不可照抄部分。
- 驗證：Markdown 本機連結與 SVG XML 解析通過；更新後 SVG 已由 headless Chrome 實際
  渲染並人工確認標籤未溢出；文件 UID/GID、Git diff 與 Docker／暫存 clone 清理通過。

## 2026-08-31：逐晶片模擬契約

- 目標：把外部參考來源與 `superacan-emu` 里程碑 1–4 的實作證據整理成可重建的逐晶片流程。
- 新增：`docs/chip-emulation-guide.md`，涵蓋整機排程、雙 CPU、SystemBus、UM6650、UM6618、
  UM6619、主 DMA、手把、即時存檔與分層驗證 gate。
- 關鍵契約：68k／65C02 3:1 時序、HALT 後 reset-vector 捕捉、IRQ 各自 ack、原子 word register、
  UM6618 indexed priority pipeline、UM6619 16.16 phase 與 44.744 kHz→48 kHz 輸出。
- 邊界：window 1、額外 VRAM、envelope、類比 DAC／NTSC encoder 仍明標假說或數位近似，未以
  類似主機行為猜補。

## 2026-08-31：Palette DAC 與晶粒逆向邊界複查

- 新來源：UM70C171 原廠資料表可證明同族 256×18-bit palette、pixel mask、`BLANK` 與三路
  6-bit DAC 架構，但沒有證據證明 UM70C188 register／pin 完全相容，因此只列研究模式參考。
- 晶粒逆向：UM6619 研究者曾報告走線與 cell boundary 約 99%，但 cell 功能尚未完成辨識；
  SiliconRE 公開狀態仍為 Stalled，沒有可用 schematic／netlist／Verilog，不能當閘級 oracle。
- 模擬策略維持：一般輸出使用已驗證的 xBGR555 digital framebuffer；類比 palette／NTSC path
  若日後實作，必須明標 approximation 並與實機 capture 分開驗證。

## 2026-08-31：軟體模擬資料充分度評估

- 結論：現有知識庫＋固定 MAME source＋deprecated C++ oracle 足以重建功能型軟體模擬器，
  並已證明三款遊戲的畫面、音訊與輸入垂直切片；不足以宣稱全庫相容或硬體逐週期精確。
- 新增 `docs/emulation-readiness-assessment.md`：逐子系統 readiness matrix、MAME 函式到規格的
  定位索引、授權邊界、缺口分類與下一個九款 ROM 相容性 gate。
- 關鍵限制：現有正式玩家路徑集中在 Boom Zoo、Monopoly、Speedy Dragon；UM6618 的部分 DMA、
  priority、sprite clipping／sizing、visible area 與 UM6619 envelope 仍缺獨立硬體證據。
- 開發現況分離：C++ oracle 證明架構可行；production 純 Go 核心仍在 68000 開工階段，不能把
  oracle 完成度冒充 Go 版完成度。

## 2026-08-31：BIOS 完整性與文件稽核

- 唯讀盤點 `Bcan008b/bios/`：兩個 ZIP 共四個預期成員，大小、CRC32、SHA-1 均與固定
  MAME `6ae579a` 的 `supracan.cpp`／`umc6650.cpp` 定義一致，功能型模擬所需檔案完整。
- 補入兩個 ZIP 容器與四個解壓成員的 SHA-256；說明 loader 應驗成員身分，不能把可因壓縮
  metadata 改變的 ZIP hash 當唯一合法值。
- 訂正舊文：`umc6650.bin` 的 CRC 已由 MAME 列出；兩個 `internal_6502` 檔是內建取樣而非
  韌體；UMC6650 內容是唯讀金鑰而非 PLD 熔絲圖；埠角色已由 IPL＋Bcan 雙重確認。
- 保留限制：ZIP 的 1996 timestamp 不是 dump 日期證據；dump 設備、來源 revision 與其他可能
  BIOS revision 仍未知，但不阻塞目前已知開機路徑。

## 2026-08-31：68k BIOS 完整流程與中斷向量

- 以 word-swap 後 SHA-256 固定輸入，用 GNU m68k objdump 完整解碼 `$400–$630`，並逐項盤點
  `$000–$3FF` 的 256-entry vector table。
- 新增 `docs/bios-control-flow.md`：UM6650 RAM／key、卡帶授權兩階段、失敗路徑、overlay
  轉交、完整 exception／autovector 表與模擬器測試契約。
- 中斷結論：level 1–7 各指向 `$624–$630` 的單一 `RTE`；其餘 vectors 幾乎全指向 `$622`
  的 `RTE`。BIOS 沒有週邊 service routine；遊戲 IRQ handlers 在 overlay 關閉後由卡帶提供。
- 新模擬風險：`$61E` 關高區 overlay 後仍須執行已預取的 `$620 JMP (A0)`，因此 68000
  prefetch queue 是開機轉交的可觀察契約，不能用無 prefetch 的逐指令重新取碼模型取代。

## 2026-08-31：第二輪文件與網路來源複查

- 固定 MAME `hash/supracan.xml`：補齊 F001–F012 十二款正式 catalog、serial、年份、發行商、
  中文標題、ROM hash、MAME support metadata 與未確認 NVRAM 提示。
- 以 CRC／SHA-1 定案：本地 `Super Dragon Force` ZIP 內容其實是 F007 Super Light Saga -
  Dragon Force／超級光明戰史；`08002` 成員亦為誤命名，內容匹配 `08007.1`。
- 新增 `docs/software-catalog.md` 與 `docs/documentation-review.md`；本地九款均匹配 catalog，
  缺 F009/F010/F012，正式畫面＋音訊＋輸入垂直驗證仍只有三款。
- 固定 `angelosa/hw_docs` `1b9e8fe`：補第四 normal layer、pixel/GFX mode、video flags、window
  clipping 與 IRQ1–7 observation；訂正 `$F001F0` 不是 FRC。
- 搜尋停止線：UM6618/6619 manual、UM70C188 datasheet、額外 VRAM bank、FRC 公式、envelope
  與 UM6650 pin timing 仍沒有可升格公開來源，後續應轉 ROM consumer／實機量測。

## 2026-08-31：256 KiB VRAM 最高位配線確認

- 逐 net 檢查 `superacan-notes` 固定 commit `63731a2` 的 Eagle `PPU.sch`：UM6618
  `VRAM_A1..A17` 依序接到 U5/U6 `UM611024` 的 `A0..A16`。
- 因 `VRAM_A17` 實際接到兩顆 SRAM 的最高位 `A16`，確認上半 128 KiB 在電氣上可由 UM6618
  定址，推翻「只是換成較大 SRAM、上半部未接」的候選解釋。
- 新增 `docs/vram-architecture.md`，明確區分 128 KiB CPU window 與 256 KiB physical VRAM；
  register／renderer／DMA consumer 仍未知，BIOS 因不初始化視訊硬體而無法回答。

## 2026-08-31：其他晶片板級證據方法複查

- 在無網路、唯讀 Docker 容器內解析固定 `superacan-notes` commit 的五份 Eagle schematic，
  逐 net 對照 CPU、Work RAM、VRAM、sound RAM、UM6618、UM6619、UM6650 與手把 glue logic。
- 新增 `docs/hardware-evidence-method.md`：列出每顆晶片由接線可證實的機制、仍需的
  producer／consumer 或實機證據，以及不可從其他 68000 主機類推的界線。
- 新升格的板級結論：UM6619 接完整 68k bus/control/arbitration，並產生 Work RAM byte-lane
  selects、獨占 sound RAM bus；因此它是 APU／I/O 之外的主要 system／memory controller。

## 2026-08-31：UM70C188／palette DAC 深度搜尋

- 找到 Bitsavers 保存的 UMC `UM70C171` 15 頁原廠 preliminary datasheet，記錄 SHA-256，
  擷取 palette address/color/mask、auto-increment、PCLK pipeline、blanking 與 6-bit DAC 契約。
- 與 `PPU.sch` 逐 pin 比對：實裝 U3 是 `UM70C188`，UM6618 直接驅動 P0–7、PCLK、D0–7、
  RS0/1、RD/WR、BLANK；Eagle symbol 沿用 UM70C171 不代表內部功能相同。
- 同期 VGA RAMDAC 技術資料把 UM70C188 列為 24-bit／TrueColor 類型；MAME 對 `$F001F0`
  bit 4 只提示 special pixel mode 而未實作。兩者關係列為假說，新增 `docs/palette-dac.md`，
  不將其升格成已證實 A'Can 顯示模式。
- 在 Capstone Docker 中掃描九款 word-swap 正規化 ROM：全部都有 `$F001F0` reference；
  The Son of Evil `$74C86` 明寫 `$0009`，證實正式遊戲會啟用 MAME 尚未使用的 pixel-mode
  bit 3。下一個窄任務是該 call path 與畫面／pixel bus trace，而非繼續猜 UM70C188 規格。
- 續追 F003 producer：`$74C46` 清 512-byte palette 後寫硬體 `$0009`，`$74D06` 同步建立
  `$FFFF9F20` shadow；`$27EE` 在 dirty flag bit 7 時回寫 `$F001F0`。另找到三處切 `$0001`、
  三處切回 `$0009`，證明 bit 3 是可切換狀態。新增 `docs/f003-video-mode.md` 與動態斷點契約。
- 在 sibling deprecated oracle 補純記錄 `watchpix` 後跑 F003 6000 frames，取得八筆實際
  `$F001F0` writes；`$74C86/$27EE` 與靜態資料流吻合，並觀察 `$FFFFDA5C/$FFFFDB90` 的
  Work RAM mirror producer。畫面不完整但原因可能包含其他 UM6618 缺口，未把它誤判為
  bit 3 direct-color 證據；下一步是 copy-source 定位與同 save-state A/B。
