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
