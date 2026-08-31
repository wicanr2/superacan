# F003《惡魔之子》UM6618 pixel-mode producer

更新日期：2026-08-31。本文保存 `$F001F0` pixel／GFX mode 的具名 ROM producer；不把
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

## 6. deprecated oracle 動態 trace（a，software-observed）

在 `superacan-emu` deprecated C++ oracle 的 16-bit UM6618 write path 加入純記錄探針；探針
不修改 register value、副作用或 renderer。固定同一 ROM，headless 執行 6000 frames 得到：

| Frame | Value | PC | 與靜態證據的關係 |
|---:|---:|---:|---|
| 20 | `$0009` | `$FFFFDA5C` | Work RAM mirror 中執行的早期更新／轉交程式；尚未定位原始 copy source |
| 211 | `$0001` | `$FFFFDB90` | Work RAM mirror 程式切除 bit 3；尚未定位原始 copy source |
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

動態 trace 已證實 `$0001↔$0009` 的實際硬體寫入與 `$27EE` consumer；下一步縮成兩件事：

1. 找 `$FFFFDA5C/$FFFFDB90` Work RAM code 的卡帶 copy source，補齊原始 ROM 位址；
2. 在同一 save state 對 bit 3 做一次性 A/B renderer probe，比較 frame／VRAM／palette hashes。
