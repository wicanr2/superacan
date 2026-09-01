# F003《惡魔之子》UM6618 pixel-mode producer

更新日期：2026-09-01。本文保存 `$F001F0` pixel／GFX mode 的具名 ROM producer；不把
`pixel_mode` 導覽名稱當成已證實的 UM6618／UM70C188 內部語意。

## 1. 輸入與位址空間

| 項目 | 值 |
|---|---|
| 輸入 | `The Son of Evil (Taiwan).bin` |
| raw SHA-256 | `791ab9d5ca182830fcf8ded488e71f1b61398da84967543396d0496e11bf5deb` |
| word-swap 後 SHA-256 | `4a778730c01f432b4f0acf7ef95a96775cac64c729eead22e64bbb1c80d2f54b` |
| 工具 | Capstone M68K big-endian／68000 mode（Docker `fd2-cap-local:latest`） |
| 位址基準 | 下列為 word-swap 後卡帶低區 CPU address；不與 IDA 或 raw-file byte order 混列 |

## 2. 開機初始化流程（已證實）

`$74C00` 是接續 RAM clear 的初始化序列，與 mode 直接相關的控制流如下：

```text
$74C00 platform/game initialization
  ├─ JSR $74C36   清 Work RAM 到目前 stack boundary
  ├─ JSR $74C46
  │    ├─ 設定數個 RAM pointers
  │    ├─ 清 `$F00200–$F003FF`：256 個 16-bit palette entries
  │    ├─ `$74C86`: `$F001F0 ← $0009`
  │    └─ `$F00008 ← $1080`
  ├─ JSR $74C98   建立 `$FFFF9E40` 起的視訊 shadow state
  │    └─ `$74D06`: `$FFFF9F20 ← $0009`
  └─ 後續 IRQ／遊戲初始化
```

| CPU address | bytes（word-swap 後） | 指令 | 分級 |
|---:|---|---|---|
| `$74C6E` | `287C00F00200` | `movea.l #$F00200,A4` | 已證實 |
| `$74C74` | `383C007F` | `move.w #$007F,D4` | 已證實 |
| `$74C78` | `429C / 51CCFFFC` | 128 次 `clr.l (A4)+`，清 512 bytes | 已證實 |
| `$74C86` | `33FC000900F001F0` | `move.w #$0009,$F001F0` | 已證實 |
| `$74C8E` | `33FC108000F00008` | `move.w #$1080,$F00008` | 已證實；bit 語意另查 |
| `$74D06` | `33FC0009FFFF9F20` | `move.w #$0009,$FFFF9F20` | 已證實；mode shadow 為強推論 |

`$0009` 依 MAME mask 可拆成 gfx-mode bits 0–2=`1`、未接入 renderer 的 bit 3=`1`。這證明
bit 3 是正式軟體使用值；不證明它的硬體名稱是 direct color。

## 3. frame update 回寫（已證實）

`$27B2` 起的視訊更新常式檢查 `$FFFF9C1A` dirty flags。bit 7 成立時：

```asm
$27EE  33F9 FFFF9F20 00F001F0  move.w $FFFF9F20,$F001F0
$27F8  0279 7FFF FFFF9C1A      andi.w #$7FFF,$FFFF9C1A
```

所以 `$FFFF9F20` 是會送回硬體的 register shadow。此切片尚未固定完整 IRQ 入口／level，故只稱
「視訊更新常式」，不以推測名稱取代原始位址。

## 4. mode 生命週期

全 ROM 對 `$FFFF9F20` 的 absolute references 共十處：

- 寫 `$0009`：`$74D06`、`$1B7308`、`$1B7BB4`、`$1B7C36`；
- 寫 `$0001`：`$87690`、`$1B6494`、`$1B6AEC`；
- frame update 讀出：`$27EE`；
- `$1B7A60` 讀、`$1B7AF8` 寫回：周邊會把一組 shadow state push 到 stack 再恢復，故
  save／restore 語意列為**強推論**，尚未追 caller。

遊戲會在 `$0001` 與 `$0009` 間切換 bit 3，而非永久固定。`$1B6494/$1B6AEC` 寫 `$0001`
後設定 `$FFFF9C1A` 高位 dirty flags；`$1B7308` 等路徑切回 `$0009`。具體場景仍未知，不能由
附近資料猜成標題、戰鬥或選單。

## 5. 模擬器驗證契約

MAME 只保存 `m_pixel_mode = data & 0x18`，render path 沒有讀取它。下一個最小充分驗證：

1. 對 `$87690`、`$1B6494`、`$1B6AEC`、`$1B7308`、`$1B7BB4`、`$1B7C36` 設 tracepoint；
2. 記錄 PC、寫值、call stack、frame、VRAM hash、palette hash 與截圖；
3. 同狀態比較 bit 3 on/off，判斷差異是 bpp、pixel packing、palette bypass 或其他功能；
4. 若顯示多 byte-per-pixel，再量測 UM6618→UM70C188 的 P0–P7/PCLK framing；
5. 定案前使用 `unknown pixel mode bit 3`，不得命名為 TrueColor enable。

同一款遊戲另有一條可用的外部線索：MAME driver 檔頭寫「visible area 幾乎確定是 224，因為
The Son of Evil 在 vblank handler 有明確檢查」。因此做 bit 3 的 A/B 之前，應先固定 visible
area 與 `$F00008` video flags（本檔 `$74C8E` 寫 `$1080`），避免把顯示區高度差異誤讀成
pixel mode 的效果。

## 6. deprecated oracle 動態 trace（a，software-observed）

在 `superacan-emu` deprecated C++ oracle 的 16-bit UM6618 write path 加入純記錄探針；探針
不修改 register value、副作用或 renderer。固定同一 ROM，headless 執行 6000 frames 得到：

| Frame | Value | PC | 與靜態證據的關係 |
|---:|---:|---:|---|
| 20 | `$0009` | `$FFFFDA5C` | 執行期產生的 Work RAM 程式；producer 見下節 |
| 211 | `$0001` | `$FFFFDB90` | 執行期產生的 Work RAM 程式；producer 見下節 |
| 216 | `$0009` | `$00074C86` | 與開機初始化 immediate producer 完全相符 |
| 219 | `$0009` | `$000027EE` | 與 shadow consumer 完全相符 |
| 255 | `$0001` | `$000027EE` | 動態確認 shadow 已被某 producer 改成 `$0001` |
| 3155 | `$0001` | `$000027EE` | 後續重送 |
| 3349 | `$0001` | `$000027EE` | 後續重送 |
| 5914 | `$0009` | `$FFFFDA5C` | 同一 Work RAM mirror 路徑再次寫入 |

frame 200 截圖仍是 A'Can logo；frame 212、217、220、256 為黑色過場。frame 3000 的現有 oracle
畫面只有底部琥珀色圖像帶，frame 6000 又回到 A'Can logo。這是「現有 renderer 在 F003 路徑
輸出不完整」的 software-observed 證據，但不能把缺圖唯一歸因於 bit 3：同一 oracle 尚缺第四
normal layer、部分 priority／ROZ 等行為。必須做同狀態 bit 3 A/B 才能建立因果。

### 6.1 Work RAM producer 來源

把探針擴充為同列保存 PC 起八個 16-bit words，得到兩段 RAM code 簽章：

| 執行位址 | 指令 words | ROM 比對 |
|---:|---|---|
| `$FFFFDA5C` | `33FC:0009:00F0:01F0:33FC:120E:00F0:0008` | 前五個 words 與 `$74C86` 相同，後續立即值不同；不是逐 byte 原樣 copy |
| `$FFFFDB90` | `33FC:0001:00F0:01F0:41F9:00F4:0000:303C` | word-swap 後 ROM 無完整簽章 |

再窄記錄 Work RAM `$DA50–$DA6F`、`$DB80–$DBAF` 的 byte writes：前者在 frame 15、後者
在 frame 16 生成；兩段目標 byte 均由 `$FFFF80B6` 寫入。該寫入迴圈開頭 words 為
`12C3:60E4:0028:002C`，可在 word-swap 後卡帶 ROM `$00073A54` 精確找到。frame 212 時
`$00074BF4` 所在初始化流程又將兩段清零。

`$7394E–$7399C` 另證實以 `movea.w #$8000,A5` 取得 sign-extended `$FFFF8000`，再把
`$7399E` 起的 `$19C` bytes 搬到該處；因此 ROM
`$73A54` 與 RAM `$FFFF80B6` 的位移皆為 `$B6`，是同一解碼器的 ROM／RAM 視圖，而不是
兩套偶然相同的程式。該解碼器具有可直接由指令證實的兩類輸出：

- `$73A3E–$73A54` 從 bitstream 走表解碼，leaf byte 由 `move.b d3,(a1)+` 輸出；
- `$73A6C–$73B36` 對部分 symbol 跳入 `$73A84` 起的短距離重複與 `$73B2A` 起的
  backward-copy 路徑，從已輸出資料回填。

因此可**已證實**這不是純 relocation，而是「entropy-coded literal＋LZ 類 backward copy」
的解壓路徑；「Huffman」名稱目前只列**強推論**，因樹表建構雖明顯，尚未完整形式化碼表格式。
### 6.2 本次解壓呼叫契約（已證實）

在 RAM 解碼器 `$FFFF8000` 入口與終止跳板 `$FFFF80E2` 只讀取 CPU registers，取得同一次
frame 5–16 呼叫：

| 時點 | A0 | A1 | 解釋 |
|---|---:|---:|---|
| 入口 | `$00073B44` | `$FFFFB800` | A0 指向壓縮區 header／table；A1 是輸出起點 |
| 解出 `$FFFFDA5C` | `$00074A57` | `$FFFFDA5C` | `$F001F0←$0009` producer 的生成位置 |
| 解出 `$FFFFDB90` | `$00074B63` | `$FFFFDB90` | `$F001F0←$0001` producer 的生成位置 |
| 終止 | `$00074BEC` | `$FFFFDC56` | source／destination exclusive end |

入口 `$FFFF8000` 的 `adda.w #$00A4,A0` 令實際 bitstream 起點成為 `$73BE8`。故本批壓縮
區可界定為 header／table `$73B44–$73BE7`（`$A4` bytes）、bitstream `$73BE8–$74BEB`
（`$1004` bytes），輸出 `$FFFFB800–$FFFFDC55`（`$2456` bytes）。這些界線及
`$1004 → $2456` 是 software-observed 已證實值；不能直接外推成其他資產也有相同固定長度。

因此「兩次輸入資料流」的舊描述亦需訂正：兩段 `$F001F0` producer 都位於**同一次連續解壓
輸出**，不是兩次獨立呼叫。格式家族與本批界線已足以離線重播驗證，但 tree header 的欄位定義、
symbol 編碼及通用終止標記仍未形式化，尚不能宣稱整個 F003 壓縮格式已完整解出。所有 ROM
位址沿用本文 word-swap 後低區 CPU address 基準；RAM PC 則保留實際 `$FFFFxxxx` 執行位址。

動態 trace 已證實 `$0001↔$0009` 的實際硬體寫入、`$27EE` consumer 與 RAM code producer；
下一步縮成兩件事：

1. 把 `$73B44` header／table 與 `$73BE8` bitstream 形式化成離線解碼器，逐 byte 驗證
   `$FFFFB800–$FFFFDC55`；
2. 在同一 save state 對 bit 3 做一次性 A/B renderer probe，比較 frame／VRAM／palette hashes。
