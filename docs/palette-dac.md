# UM70C188 調色盤／RAMDAC 研究

更新日期：2026-08-31。本文區分主機板實裝的 `UM70C188`、可取得的 `UM70C171` 原廠
資料表，以及 MAME 目前採用的簡化 palette model。

## 1. 晶片身分與接線（p）

`PCGAM 16000-2A` 的 `PPU.sch` 把 U3 的 value 記為 **UM70C188**；Eagle symbol 沿用
`UM70C171`，symbol 名不能反向證明兩者功能相同。板級 nets 顯示 UM6618 直接連接 U3：

| UM6618 | U3 | 已確認角色 |
|---|---|---|
| `DAC_P0..P7` | `P0..P7` | 8-bit pixel／palette-index path |
| `DAC_PCLK` | `PCLK` | pixel latch clock |
| `DAC_D0..D7` | `D0..D7` | register／palette programming data bus |
| `DAC_RS0/RS1` | `RS0/RS1` | register selection |
| `DAC_!RD/!WR` | `RD/WR` | 非同步 register read／write strobes |
| `DAC_!BLANK` | `BLANK` | video blanking |
| `RED/GREEN/BLUE` | KA2195D／輸出網路 | analog RGB output |

這證明 UM6618 產生 pixel data、clock、programming 與 blanking；U3 負責 palette／DAC 階段。
它不證明 UM70C188 隱藏 command register 或 direct-color mode 如何啟用。

## 2. UM70C171 原廠契約（r）

目前找到的原始資料是 UMC 15 頁 preliminary datasheet：
[UM70C171 Color Palette With Triple 6-Bit DAC](https://www.bitsavers.org/components/umc/UM70C171.pdf)。
本輪下載檔 SHA-256：
`777d982cd4b7259b7657cbc4debaf82caf3c563e28ad14119ad25f66b900805e`。

它可解釋與 U3 pin-compatible 的基本介面：

- 256×18-bit palette、三個 6-bit DAC、最高 35 MHz pixel rate；
- P0–P7 在 PCLK rising edge latch，經 pixel-mask register 後索引 palette；
- `RS0/RS1=00`：Pixel Address write；`11`：Pixel Address read；`10`：Color Value；
  `01`：Pixel Mask；
- Color Value 依 red、green、blue 三次 6-bit transfer 組成，之後 palette address auto-increment；
- `BLANK` active-low，使 analog outputs 為黑，但不阻止更新 palette；
- 三級 pipeline；非 blank 期間改 palette 可能造成最多兩個 PCLK 的非預期 output。

這些只能作 UM70C188 基本 pin-compatible path 的參考，不可把 UM70C171 的 palette 容量、
command mode 或色彩格式直接宣稱為 UM70C188 已證實行為。

## 3. UM70C188 與特殊像素模式

同期 VGA RAMDAC 資料把 `UM70C171` 列為標準 256-color DAC，`UM70C178` 列為 15/16-bit
HiColor，`UM70C188` 列為 24-bit／TrueColor 類型：

- [VGADOC RAMDAC.TXT mirror](https://github.com/whatisaphone/tower-pc/blob/master/docs/video/vgadoc4b/RAMDAC.TXT)；
- [DOS Days UM85C408 板卡實物研究](https://www.dosdays.co.uk/topics/retro_review_um85c408_pt1.php)。

這些不是 UM70C188 原廠資料表，只列為研究線索。它們與 A'Can 證據形成下列候選鏈：

1. 主機板 U3 確為 `UM70C188`（p）；
2. MAME 把 UM6618 `$F001F0` bits 3–4 保存為 `pixel_mode`，但 render path 完全未使用它們；
   bit 4 只額外顯示 `Special pixel mode enabled!`（b）；
3. 因此這兩 bits 可能控制 U3 high／true-color path，屬**假說**，尚無 pixel
   waveform 或 UM70C188 programming sequence 證明。

不能因此把「同時 256 色」改成「已證實 24-bit 顯示」。U3 的 P0–P7 只有 8-bit pixel input，
direct-color 通常需要多個 PCLK 或特殊 multiplexing；真正 framing 必須由 trace 或資料表確認。

## 4. 模擬器驗證順序

安全基線仍是已驗證的 256-entry `xBGR555` palette：

1. 追蹤十二款 ROM 對 `$F001F0` 的寫值、呼叫點與畫面情境；
2. trace UM6618 對 U3 的 `RS0/RS1/RD/WR` sequence，尋找 command-mode unlock；
3. 若有 bit 4 consumer，擷取 `P0..P7` 與 PCLK，判斷單 pixel 是一次或多次 transfer；
4. normal indexed mode 與 experimental direct-color mode 分開；未取得同狀態畫面前不得讓
   假說進入正式 renderer；
5. 類比精確度另以 BLANK、pipeline latency、IREF 與 KA2195D output capture 驗證。

## 5. 證據分級

- **已證實**：U3 型號、UM6618↔U3 基本 pins、indexed palette 的現行軟體行為。
- **強推論**：UM70C171 datasheet 可描述 UM70C188 的 pin-compatible 基本介面。
- **假說**：`$F001F0` bits 3–4 控制 UM70C188 high／true-color path。
- **唯一的軟體 consumer 指向別的方向**：MAME 不消費 bits 3–4；Bcan 只在 ROZ 層消費
  bit 3——當 pixel mode 恰為 `$08` 且 ROZ 處於 8bpp region 時，該層改成**線性 bitmap**，
  跳過 tilemap 與 tile 圖形，直接以 `4 × $F00196` 為基底逐像素讀 VRAM（指令位址、公式與
  自製 ROM 對照實驗見 [f003-video-mode.md](f003-video-mode.md) §7.3、§7.6）。
  也就是說，在唯一實作它的程式裡，bit 3 是 ROZ 的 tilemap／bitmap 切換，不是全域
  direct color。這削弱本假說，但因為 Bcan 的解讀同樣沒有硬體佐證，兩者都要靠實機訊號
  才能定案。
- **bit 4 已量測**：`homebrew/pixelmodeprobe/` 四相位掃描顯示 bit 4 沒有獨立效果，
  只是 bit 3 的排他條件（pixel mode 必須恰為 `$08`）。兩個位元都沒有全域色彩作用，
  本假說再被削弱一層。
- **未知**：UM70C188 command registers、multiplexing，以及正式遊戲是否使用特殊模式。

## 6. 本地 ROM producer 掃描（a，靜態）

九款本地 ROM 全部含 `$F001F0` absolute reference，證明它是實際使用的 mode register，而非
僅存在於 MAME 的推測欄位。16-bit word-swap 正規化後，可直接確認的 immediate writes 為：

| 遊戲 | 檔案 offset | 寫值 | 解讀邊界 |
|---|---:|---:|---|
| The Son of Evil | `$74C86` | `$0009` | gfx mode 1＋**pixel-mode bit 3**；本地唯一立即值明確啟用 pixel bit |
| Formosa Duel | `$5F7A` | `$0001` | gfx mode 1 |
| Journey to the Laugh | 多處 | `$0001`、`$0041` | low gfx mode 1；bit 6 語意未列入 MAME pixel mask |
| Monopoly | `$3802` | `$0001` | gfx mode 1 |
| Boom Zoo | `$2462` | `$0001` | gfx mode 1 |
| Sango Fighter | `$3868/$5B90` | `$0003` | gfx mode 3 |

Formosa Duel、Speedy Dragon、Super Taiwanese Baseball League 與 Journey 另有由 register／RAM
載入的動態寫值，不能靠 immediate scan 列舉完整集合。The Son of Evil 的 `$0009` 把研究目標
由「是否有遊戲使用」縮小為具名 consumer；下一步應 trace `$74C86` 所在初始化路徑、對應畫面
與 P0–P7/PCLK framing。這仍不證明 bit 3 就是 direct color，但已證明特殊 pixel bit 不是閒置。

初始化、frame update shadow 與 `$0001↔$0009` 切換詳見
[f003-video-mode.md](f003-video-mode.md)。
該文件也已加入 6000-frame oracle trace；結果證實切換發生，但尚未證實 direct-color 因果。
