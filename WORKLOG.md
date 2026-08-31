# 工作歷程

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
