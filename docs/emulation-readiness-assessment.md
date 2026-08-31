# Super A'Can 軟體模擬資料充分度評估

評估日期：2026-08-31。評估對象是本知識庫、固定 MAME commit
`6ae579aed3107c0b42c1c1c5cb05c02df4456eff`，以及本機 `superacan-emu` 的 deprecated C++
oracle 與純 Go 重寫現況。本文件判斷「資料能支持什麼」，不以實作存在反向宣稱原機事實。

## 1. 結論

**足夠建立功能型軟體模擬器；不足以宣稱全軟體相容、逐週期正確或實機精確。**

更具體地說：

| 目標 | 判定 | 理由 |
|---|---|---|
| 建立可開機的 emulator core | **足夠** | 兩顆 CPU、完整主要 bus map、IPL overlay、UM6650、ROM 格式與時脈已有 (a) 證據 |
| 讓數款遊戲進入正常可操作畫面 | **已證明可行** | C++ oracle 已讓 Boom Zoo、Monopoly、Speedy Dragon 通過畫面、音樂與按鍵垂直切片 |
| 重建主要影像／音訊／輸入晶片的軟體可見契約 | **大致足夠** | MAME 提供骨架，Bcan／BIOS／遊戲 driver 已修正關鍵時脈、IRQ、reset、DMA 與 UM6650 差異 |
| 全部已知 ROM 可玩 | **尚不足** | 本庫有約 9 個映像，正式驗證集中在 3 款；其餘缺正常玩家路徑與長時間回歸 |
| MAME 等級以上的廣泛相容性 | **尚不足** | C.U.G.、台灣職棒、惡魔之子等 MAME 已知缺陷尚未逐一建立 consumer／畫面證據 |
| 實機精確／逐週期模擬 | **不足** | 無 UM6618／UM6619 完整資料表、公開 netlist、logic analyzer trace 或同狀態實機 capture |

因此目前合理產品聲明應是「研究型、可運行的功能模擬器」，不能寫成「完整模擬」或
「100% 相容」。

## 2. 逐子系統 readiness matrix

| 子系統 | 文件／oracle 是否足夠實作 | 現有驗證 | 剩餘風險 | 判定 |
|---|---|---|---|---|
| MC68HC000 | 是；型號、10.738635 MHz、bus callback、IRQ／overlay 已知 | IPL＋三款遊戲長跑 | 新純 Go core 尚須完整 opcode、prefetch、exception 與 phase tests | **實作資料 READY；新核心未完成** |
| W65C02 | 是；型號、3.579545 MHz、memory map、HALT/reset、IRQ ack 已知 | 兩套音效 driver 與 mailbox 實跑 | 純 Go core 尚未接入；少數 I/O 位元未知 | **實作資料 READY** |
| SystemBus／RAM／ROM | 是；主要 24-bit map、mirror、open bus、SRAM、word-swap 已知 | IPL、DMA、三款 ROM | wait state／bus arbitration 未達硬體級 | **功能型 READY** |
| UM6650 | 是；key、address/data port、RAM 與 IPL consumer 已知 | 兩款以上 IPL 完成交握與授權 | `$09/$0C` 對外 pin 語意未知 | **開機路徑 CONFORMED；電氣語意未知** |
| 主 DMA／sprite DMA | 主模式足夠；兩通道與常用 control 已知 | 曾以 word 原子寫入修正雙觸發，三款回歸 | 台灣職棒使用的未模擬 DMA type、精確 bus ownership／完成時間 | **常用途徑 READY；完整模式不足** |
| UM6618 | 三 tilemap、ROZ、sprite、window 0、palette 與 IRQ 足夠 | 三款截圖；logo、標題、ROZ、sprite 路徑 | 第四層、sprite sizing/clipping、priority/color mix、部分 ROZ table、逐掃描線更新、window 1 | **可用但不完整** |
| UM6619 | 16 PCM channel、pitch、key、volume、loop、DMA、timer 足夠 | 三款 WAV 非靜音、頻譜、按鍵後場景 | envelope `$A0–$DF`、真實增益／濾波、部分 register 位元 | **可聽功能 READY；音色精度不足** |
| 手把 | P1/P2 shift 與 direct mode 足夠 | P1 正常 UI 路徑；P2 register 注入 | P2 實際雙人遊戲流程、實體 adapter timing | **功能型 READY** |
| 視訊／音訊輸出 | RGBX framebuffer、44.744→48 kHz pipeline 足夠 | SDL/headless screenshot/WAV | UM70C188、KA2195D、LF347 類比效果未模擬 | **數位近似 READY** |
| Save state | 自有格式與需保存狀態已知 | 3000 幀存檔＋重載 60 幀與連跑逐 byte 相同 | 純 Go phase queue、DMA 中途 state 尚須重建；不相容 Bcan payload | **oracle 可用；新核心待做** |

`READY` 在此只代表資料足以授權功能型實作；`CONFORMED` 只用於已有同一路徑可重播證據的
項目，並不表示 confirmed-hardware。

## 3. MAME source 可如何重建成文件

MAME source 是目前最完整的公開硬體行為骨架，但其 driver 自己標記
`MACHINE_IMPERFECT_SOUND | MACHINE_IMPERFECT_GRAPHICS`，檔頭也明列圖形缺陷。因此應採
「source → DRAFT 規格 → 本庫 (a) 證據校正 → 遊戲 consumer 驗證」流程，不可直接把程式碼
翻成散文後標成硬體事實。

### 3.1 原始碼到規格的定位索引

| MAME 原始定位 | 可重建的文件內容 | 需要本庫修正／補證 |
|---|---|---|
| `supracan_state::main_map` | 68k address decode、ROM／RAM／device window | Bcan 的 Work RAM、SRAM、越界讀與 overlay 行為 |
| `supracan_state::sound_map` | 65C02 RAM／I/O map | `$0411` 不清全部 IRQ；六來源各自 ack；latch 空值與觸發 |
| `supracan_state::dma_w` | 主 DMA register、count、增減與間接模式 | word transaction 原子性、已觀察 control 組合、未知 type |
| `video_r`／`video_w` | UM6618 register readback／副作用 | 未知 register 保留；MAME TODO 不得升格 |
| `video_start`＋`gfx_supracan` | 8/4/2/1-bpp tile layout、tilemap 尺寸 | 1-bpp alternate address swap 是 BIOS logo 特例／近似 |
| `get_tilemap_info_common` | tile index、bank、palette、flip | 用多款 ROM 的 producer／畫面確認 gfx mode |
| `draw_sprites` | sprite entry、尺寸表、bank、mask、priority | scanline clipping、sizing 與邊界仍未完整 |
| `draw_roz_layer` | affine 係數、scroll、wrap、逐行 table | MAME 自標 HACK 的路徑只能列 MAME-derived |
| `screen_update`／`scanline_cb` | 圖層合成、visible area、raster／vblank | 10.738635 MHz 時脈、HOLD_LINE、不同遊戲的 224／240 線需求 |
| `update_frc_state` | FRC 已知 case table | 公式是 MAME HACK，不能稱硬體 timer 規格 |
| `umc6619_sound_device::*` | 16-channel PCM、pitch、address、volume、timer、DMA IRQ | envelope 未實作；以遊戲 driver 修正 reset／IRQ／mailbox |
| `umc6650_device::*` | key ROM、內部 RAM、address latch | MAME 把 `$EB0D01/$EB0D03` 埠角色解反；以 IPL (a) 為準 |
| `devices/bus/supracan/*` | 卡帶 slot、raw ROM 與 SRAM 骨架 | Bcan 雙部分 ROM、word-swap、固定 32768-byte SRAM |

### 3.2 每個重建條目的固定格式

從 MAME 重建的新條目至少同列：

1. 固定 commit、檔案與函式／case 位址；
2. register address、資料寬度、讀寫副作用與 reset value；
3. MAME 的實作行為與原始註解／TODO；
4. 本庫是否有 Bcan、BIOS 或 ROM producer／consumer 佐證；
5. 衝突時採用哪一方及原因；
6. 證據級別：MAME-derived、confirmed-Bcan、software-observed、strong-inference 或 unknown；
7. 最小重播測試與玩家可見結果。

這能把 MAME 當成可追溯規格來源，同時避免把已知 HACK、錯誤時脈或錯誤 ack 行為帶入新核心。

### 3.3 授權邊界

本次固定的 `supracan.cpp`、`umc6619_sound.*`、`umc6650.*` 檔頭為 BSD-3-Clause。可以閱讀、
引用行為並重新實作；若直接複製受保護程式碼，必須保留該檔案的版權與授權通知。MAME 整體
包含多種 GPL-compatible 授權，不能僅憑三個檔案的 BSD 標頭推定任意依賴或整個 framework
都是 MIT-compatible。純 Go 核心目前採「文件化行為＋獨立實作」，是較乾淨的依賴邊界。

## 4. 現在不能宣稱完成的原因

### 4.1 軟體覆蓋不足

現有 ROM inventory 約 9 個映像，但具完整畫面＋音訊＋輸入收據者只有 3 款。至少還需對
Formosa Duel、Journey to the Laugh、Sango Fighter、Super Dragon Force、Super Taiwanese
Baseball League、The Son of Evil 分層抽樣。僅能進入 entry point 或顯示一張畫面不算可玩。

### 4.2 MAME 自己仍列出的硬體缺口

固定 driver 明列 sprite sizing／scanline clipping、1-bpp ROZ、ROZ scaling table、priority、
第四層、部分 DMA、window／visible area 與多款遊戲畫面問題。部分缺口已被本專案 oracle 改善，
但未經全庫回歸或實機比較者不能自動視為解決。

### 4.3 缺少獨立實機 oracle

目前最強證據多為 Bcan、MAME、BIOS 與 ROM software consumer。這足以做高品質功能模擬，卻
不足以決定：精確 scanline／dot 時序、DMA bus stealing、混音削波、類比 RGB／composite、
未被已知遊戲使用的 register，以及晶片內部架構。

## 5. 建議的下一個完成閘門

在新增更多硬體猜測前，先做軟體相容性垂直抽樣：

1. 固定 9 個 ROM／BIOS 的 SHA-256 與預期入口；
2. 每款保存「開機 → 標題 → 可操作畫面」的 input timeline、frame hash、audio hash 與截圖；
3. 有雙人、存檔或替代驅動的遊戲，各抽一條第二路徑；
4. 對失敗項保存 bus／IRQ／DMA 最後事件，分類成 implementation、RE 或 dynamic-oracle 缺口；
5. 優先處理 Super Taiwanese Baseball League 的 DMA、The Son of Evil 的 priority／visible area，
   因它們最可能揭露現有模型的結構性不足；
6. 全庫至少通過正常標題與輸入後，才能把狀態從「數款可運行」提升為「廣泛相容」。

若目標是一般可玩模擬器，以上 gate 比追逐 UM6619 晶粒 netlist 更有價值；若目標改成逐週期
硬體保存，則需要新的實機量測與晶粒證據，現有文件本身無法補足。
