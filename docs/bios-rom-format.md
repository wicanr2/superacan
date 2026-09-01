# BIOS 與 ROM 格式分析

> 來源：**(a)** 級——對 `Bcan008b/bios/*.zip` 與 `Bcan008b/ROMS/` 的直接
> hexdump 觀察（2026-08-30）；雜湊值與 MAME driver 記載交叉驗證 **(b)**。
> 依工作守則不複製大段版權內容，只記錄位址、向量值與結構觀察。

## 1. BIOS 檔案

`supracan.zip` 與 `umc6650.zip` 的四個成員，其大小、CRC32 與 SHA-1 均和固定
MAME commit `6ae579a` 的 `supracan.cpp`／`umc6650.cpp` ROM 定義**完全一致**，
確認本 repo 的 BIOS dump 即 MAME 使用的同一組：

| ZIP／成員 | 大小 | CRC32 | SHA-1 | SHA-256 |
|---|---:|---|---|---|
| `supracan.zip`／`internal_68k.bin` | 4096 | `8d575662` | `a8e75633662978d0a885f16a4ed0f898f278a10a` | `2e4d88bec69b5e7e4803368c233ce0d20f6dd107c5af0cfcc0089d310c695d7c` |
| `supracan.zip`／`internal_6502_1.bin` | 8192 | `fc9fb05f` | `8bf17bf311afeb9974bee058ba63eef5e8b6f5c1` | `219f51bcb8544fe733bf784e087544f97aa5457945260c7fa07a8639f30f3a68` |
| `supracan.zip`／`internal_6502_2.bin` | 8192 | `bf950ab7` | `ab8f15506308b89d2f8ef01b88aa2595d4e1e779` | `9889590805a97b7bb439d853d9ae4d6b31067bacb8225ab0538f3491dedab4b8` |
| `umc6650.zip`／`umc6650.bin` | 16 | `0ba78597` | `f94805457976d60b91e8df18f9f49cccec77be78` | `f158d83be6e73389967c6dadfd5160bb742e09212a1b218fb829bae3b4961b28` |

本機 ZIP 容器 SHA-256：

- `supracan.zip`：`fd79fd61b2e39a89d62ba91e1c9847d867e4d946edb808e9161f38df1d95461c`
- `umc6650.zip`：`c354a4125ceaf2405c19e12104970f5da074dca1ac9270be235b56f24064727d`

模擬器應以**成員檔名＋解壓大小＋CRC／內容雜湊**辨識 BIOS，不應把 ZIP 容器 SHA-256
當唯一合法值；相同成員可因壓縮器、排列與 metadata 不同而產生不同容器雜湊。本機 ZIP
成員時間戳均為 1996-12-24，但這類 archive metadata 不足以證明製造、dump 或發行日期，
只作本機容器盤點。

### 1.1 完整性判定與仍缺的來源資訊

就功能型模擬器而言，這組 BIOS **檔案完整**：四個 MAME 定義成員都存在，沒有缺檔、
截短或 CRC 不符。仍未知的是 dump provenance（實際取樣設備、dump 日期、主機板／晶片
revision）以及是否存在其他 BIOS revision；這些是保存來源缺口，不阻塞目前已知軟體開機。

### 1.2 internal_68k.bin（68k IPL，4 KB）

- MAME 以 `ROM_LOAD16_WORD_SWAP` 載入，映射於 68k 空間
  `$000000–$000FFF` 與 `$F80000–$F80FFF`（開機視圖）。因此檔案需做
  **16-bit 位元組交換**才是實際 68k 映像。Bcan 的「reset-vector
  interpretation」正規化字串 (a) 佐證此交換行為。
- 交換後向量表觀察（只記結論）：
  - 向量 0（初始 SSP）= `$00FD000A` —— 落在 Work RAM mirror 區
    （`$FC0000` 起 mirror 0x30000，見 memory-map.md §2），合理。
  - 向量 1（初始 PC）= `$00000400` —— 指向 IPL 自身 offset $400，
    即前 1 KB 為向量表與資料、$400 起為程式碼（推測，**待查證**）。
  - 向量 2 起多數填入 `$00000622`（交換前 `0000 2206`），應為共用
    預設例外處理常式。
- IPL 流程初判：reset → SSP/PC 取自本 ROM → 初始化（含 UMC6650 lockout
  檢查）→ 跳卡帶入口。Bcan 的「bounded BIOS boot did not reach the
  cartridge entry」(a) 證明開機末端須轉交控制權給卡帶。
  **反組譯已完成**，見 [bios-68k.md](bios-68k.md)。
- 實體位置線索（尚未定案）：`superacan-notes` 的作者說明把開機碼描述為存放在 UM6619 內部
  （「code which store inside 6619 chip」），MAME 對 `$E9001C` bit2 亦註記
  「internal ROM lockout?」。兩者相容，但目前沒有 die shot 或量測直接證明這顆 4 KiB ROM
  位於 UM6619 而非 UM6618，故僅列線索。

### 1.3 internal_6502_1/2.bin（各 8 KB）——**已查明：非程式，是取樣資料**

- MAME 載入到 `internal6502` region（兩塊連放共 16 KB），
  `machine_reset()` 時**整塊複製進 65C02 共享 sound RAM `$0000–$3FFF`**；
  die shot（Furrtek）上可見 68k ROM 旁另有兩塊 ROM。
- 內容統計（相鄰取樣強相關）+ MAME 註解確認為**音訊取樣資料**：
  檔 1 `$0000–$0FFF` 全 0（僅 `$040F`=`$08`），`$1000+` 與檔 2 全部為
  取樣。檔尾不像向量的疑問就此解開——本來就沒有向量。
- 65C02 程式由卡帶（68k）經 `$E80000` 上傳、寫 `$E9001C` bit0 釋放
  HALT。詳見 [bios-65c02.md](bios-65c02.md)。

### 1.4 umc6650.bin（16 bytes）

- 內容：12 byte ASCII `UMC 1994 (C)` + 4 byte 二進位（`90 70 65 9B`）。
- 判斷：不是 PLD 熔絲圖，而是 UMC6650 內部 `$20–$2F` 的**唯讀金鑰**。
  IPL 由 `$EB0D03` 選址、`$EB0D01` 讀資料，反向讀回 16 bytes 後驗證 ASCII
  與四個校驗 byte；確切流程已由反組譯及 Bcan bus 實作確認，見
  [bios-68k.md](bios-68k.md#3-umc6650-協定a由-ipl-反組譯推得)。仍未知的是
  `$09/$0C` 對卡帶 pin 的完整電氣語意，而非金鑰用途。

## 2. ROM（卡帶）格式

### 2.1 總則

- Raw binary，**無任何模擬器外加標頭**（無 iNES 式 header），offset 0
  即 68k 向量表。
- 與 BIOS 相同，流通 dump 為 **16-bit 位元組交換**格式（MAME 卡帶也用
  word swap 載入）。交換後 offset 0 = 初始 SSP、offset 4 = 初始 PC。
- 8 款流通 ROM 的向量觀察（交換後）：

| 遊戲 | 大小 | 初始 SSP | 初始 PC |
|---|---|---|---|
| Boom Zoo | 512 KB | $00FCFFFE | $00000412 |
| Formosa Duel | 1 MB | $00FCFEFC | $00002416 |
| Monopoly: Adventure in Africa | 1 MB | $00FCFE00 | $000024C6 |
| Sango Fighter | 3 MB | $00FCFE00 | $0000250A |
| Speedy Dragon | 2 MB | $00FCFE00 | $00000C4A |
| Super Taiwanese Baseball League | 2 MB | $00FFFFFE | $00024BE8 |
| Journey to the Laugh | 2 MB | $00FFFFFE | $001ED2DE |
| The Son of Evil | 2 MB | $00FFE0FF | $00073904 |

- 所有 PC 都落在卡帶 ROM 範圍內 → **卡帶自帶完整向量表與入口，不依賴
  BIOS 提供遊戲入口**。SSP 指向 Work RAM（含 mirror 區 `$FF0000` 寫法，
  呼應 MAME 的 `mirror(0x30000)`）。
- **無 MD/SFC 式文字標頭**：向量表之後直接是程式/資料，找不到遊戲名、
  廠商字串等 metadata（抽查前 256 byte）。遊戲識別只能靠整檔 hash
  （Bcan 即如此做，用 SHA-256）。

### 2.2 Bank 切換 / mapper

- MAME 的卡帶裝置（`bus/supracan/rom.h`，`SUPERACAN_ROM_STD`）只有
  "std" 一型：低區 `$000000–$3FFFFF` 與高區 `$F80000–$FBFFFF` 直接映射，
  **無 mapper/bank 切換暫存器**。3 MB 的 Sango Fighter 也裝得下
  （4 MB 空間）。
- Bcan 字串中亦無 mapper/bank 相關訊息 (a)。→ 目前證據：**無 mapper**。

### 2.3 雙部分卡帶（3 MB 合版）

- 本地歷史名稱 `Super Dragon Force (Taiwan).zip` = `16007 (Taiwan).bin`（2 MB）+
  `08002 (Taiwan).bin`（1 MB）。
- Bcan 規則 (a)：雙部分 ZIP 必須是一個數字 `.0` 部分 + 一個數字 `.1`
  部分；字串特別驗證「Super Light Saga」需 `16007.0`(2 MiB)+`08007.1`
  (1 MiB)。內容 CRC32／SHA-1 已確認本地兩檔分別精確匹配 MAME F007 的
  `16007.0`／`08007.1`；因此本地 ZIP 與 `08002` 成員是**誤命名**，內容確定為
  `slghtsag`（Super Light Saga - Dragon Force／超級光明戰史）。完整 hash 見
  [software-catalog.md](software-catalog.md#3-f007-雙部分卡帶訂正)。

### 2.4 卡帶 SRAM

- 掛在 `$EC0000–$ECFFFF`（8-bit），Bcan 存檔固定 32768 byte (a)。
- MAME catalog 對 F003/F005/F007/F008/F009/F012 宣告 32 KiB NVRAM，但均註明容量未確認，
  F009 連存在與否也未確認；這是 emulator fallback 提示，不是實體卡帶板級證據。

## 3. 後續工作

- [x] 反組譯 internal_68k.bin（word-swap 後），釐清 IPL 與 UMC6650 協定
  → [bios-68k.md](bios-68k.md)（2026-08-30，以 m68k-linux-gnu-objdump
  反組譯；UMC6650 埠順序、卡帶 `$2000` 授權比對均已確認）。
- [x] 反組譯 65C02 兩塊韌體 → [bios-65c02.md](bios-65c02.md)：結論為
  **取樣資料非程式**，映射到 sound RAM `$0000–$3FFF`；mailbox 協定維持
  (b) 級（MAME），細節需反組譯遊戲上傳的 65C02 代碼（後續工作）。
- [x] 以一款 ROM 的向量入口驗證 word-swap 解讀：**已驗證**。Boom Zoo
  入口 $412 與 Monopoly 入口 $24C6 交換還原後皆為合法 68k 指令序列
  （RTE/ADDQ.W/MOVE.W/MOVEA.L/JSR/CLR.W/LEA），且開機程式直接存取
  `$E90010`（UM6619 host port）、`$FCxxxx` Work RAM 與 `$FFxxxx` mirror——
  同時獨立印證 memory-map.md 的映射。
  （環境無 m68k binutils，以 opcode 手工比對確認。）
