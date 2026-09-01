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

這個 A/B 需要一個會消費 bit 3 的 renderer；§7 已確認目前兩個公開實作都沒有。

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

## 7. `$F001F0` 在 Bcan 的完整資料流（2026-09-01，IDA 反編譯 + 反組譯逐條驗證）

`$F001F0` 的兩個欄位在 Bcan 0.0.8b 裡都有 renderer consumer，且 **bit 3 只影響 ROZ 層**。
以下每一步都以指令位址佐證，不只依賴 Hex-Rays 的偽碼。

### 7.1 解碼與傳遞

| 位址 | 動作 |
|---|---|
| `sub_1400A8FA0` → `sub_1400A9200` | 寫入時拆欄位：`*(BYTE *)(video+594) = value & 0x18`（pixel mode）、`*(BYTE *)(video+595) = value & 7`（gfx mode），與 MAME 相同 |
| `sub_1400A96E0` | 狀態一致性驗證器：比對 `(reg$1F0 & 0x18) == byte@594`、`(reg$1F0 & 7) == byte@595` |
| `sub_140082130` | 每幀 snapshot 建構器：`mov rax,[rdx+29324h]`（video+588..595）→ `shr r8,30h` → `mov [rcx+0BEh],r8w`，把 **pixel mode 放進 snapshot+190、gfx mode 放進 snapshot+191** |
| `sub_14009D6E0` | renderer：輸入只有 snapshot 與輸出緩衝（`a3 == 76800` 即 320×240） |

全 `.text` 掃描 snapshot 這兩個 byte 的存取，各自只有一個讀取點：
`14009F422 movzx eax, byte ptr [rbp+0BFh]`（gfx mode）與
`14009FA8D movzx eax, byte ptr [rcx+0BEh]`（pixel mode），兩者都在 renderer 內。

### 7.2 gfx mode（bit 0–2）：與 MAME 相同的圖層 region 表

renderer 的 tilemap 迴圈用 `gfx_mode & 7` 查表得到 tile region，再由 region 換成色深：

| 圖層 | 表（立即值） | 內容 |
|---|---|---|
| 0 | `0x01000102` | `{2,1,0,1,0,0,0,0}` |
| 1 | `0x0202020201010102` | `{2,1,1,1,2,2,2,2}` |
| 2 | 常數 | 恆為 `2` |

`byte_140424B88 = {8,4,2,1,1,0,0,0}` 把 region 換成 bits per pixel，pixel mask 則是
`~(-1 << bpp)`。這三張表與 MAME `get_tilemap_region()` 的 `layer0_mode`／`layer1_mode`／
layer 2 常數完全一致，因此 **Bcan 與 MAME 在 gfx mode 上沒有分歧**。

### 7.3 pixel mode（bit 3–4）：ROZ 層的替代路徑

renderer 的 ROZ 區塊（`snapshot+112 == 1` 即 ROZ 致能）計算一個旗標：

```c
LODWORD(v445[0]) = 0x00010204;                       // {4,2,1,0}
v262 = *((_BYTE *)v408 + 190) ^ 8;                   // pixel_mode ^ 8
v429 = *((unsigned __int8 *)v445 + (roz_mode & 3));  // ROZ region
v263 = ((unsigned __int8)v429 | v262) == 0;          // region==0 且 pixel_mode==8
```

`{4,2,1,0}` 經 `byte_140424B88` 換算即 `(roz_mode & 3)` → `{1bpp, 2bpp, 4bpp, 8bpp}`，
與 MAME 的 ROZ tile region 對應相同。所以

> **`v263` 為真的條件是：`$F001F0` 的 pixel mode 恰為 `$08`（bit 3 設、bit 4 清），
> 且 ROZ 層處於 8bpp region。**

該旗標改變 ROZ 的兩件事（已證實由它選擇；為何如此仍未定案）：

1. **逐像素多一次 VRAM 查表**：以 ROZ tile bank（raw `$196`）為基底再取一個像素，
   與 ROZ tile mode（raw `$182`）低 4 bit 的 palette bank 合成，測試不通過就跳過該像素。
2. **逐行參數取值改形式**：走 24-bit（3 byte）的逐行取值，且**不加**全域 ROZ scroll 基底；
   旗標為假時則是原本的 16-bit 形式加基底。

MAME 完全不消費 pixel mode（`m_pixel_mode` 只用於 `$1F0` 讀回與 bit 4 的 popmessage），
所以這條路徑是 **Bcan 獨有**，證據等級 `confirmed-Bcan`。

### 7.4 對既有假說的影響

F003 寫 `$0009` = gfx mode 1 ＋ bit 3，而該遊戲確實使用 ROZ，與 7.3 的條件相符。
在唯一會消費該位元的實作裡，bit 3 是**ROZ 層的模式選擇**，不是全域 direct-color 開關；
這削弱（但未推翻）「bits 3–4 控制 UM70C188 high／true-color path」的假說——
Bcan 的解讀本身也沒有硬體佐證，它可能只是作者為了讓某些畫面正確而選的模型。

實測 20 張 Bcan 截圖（The Son of Evil，每 6 秒一張共 2 分鐘）相異顏色數為
1／15／82／15／14／13／14／14／60／58／58／59／58／59／1／15／118／15／14／14，
全部遠低於 256，與「bit 3 在 Bcan 裡不是 direct color」一致。

### 7.5 該分支在已知軟體上不會被走到（動態量測）

靜態上存在 consumer，不等於執行期會用到。以本專案模擬器加純記錄探針，統計每幀合成時
`(reg$1F0 & 0x18) == 0x08`、ROZ 致能、`(roz_mode & 3) == 3`（8bpp）三者是否同時成立：

| ROM（1200 幀） | pixel bit 3 幀數 | ROZ 致能 | ROZ 8bpp | 三者同時成立 |
|---|---:|---:|---:|---:|
| Boom Zoo | 191 | 191 | 0 | **0** |
| Monopoly | 192 | 355 | 0 | **0** |
| Speedy Dragon | 191 | 781 | 0 | **0** |
| Formosa Duel | 191 | 191 | 0 | **0** |
| Sango Fighter | 192 | 191 | 0 | **0** |
| Journey to the Laugh | 191 | 191 | 0 | **0** |
| Super Taiwanese Baseball League | 191 | 1052 | 0 | **0** |
| The Son of Evil | 231 | 1136 | 759 | **0** |

The Son of Evil 是唯一會讓 ROZ 進入 8bpp 的一款，延長到 6000 幀後仍然是
`pixel bit 3 = 317`、`ROZ 8bpp = 4274`、**同時成立 0 幀**——兩種狀態在時間上不重疊。

另有一個副產品觀察：八款 ROM 開頭都有約 191 幀處於 `pixel mode == $08`，且該期間 ROZ 以
1bpp 運作，對應各遊戲共用的 A'Can 開機 logo 段落。也就是說 bit 3 在實務上與 1bpp ROZ
一起出現，而 Bcan 的分支要求 8bpp，兩者互斥。

**因此結論分成兩層，不可混用**：Bcan 的程式碼裡有 bit 3 的 consumer（§7.3 的指令佐證），
但在本地八款 ROM 的可觀察路徑上該分支**從未執行**。就模擬器實作而言等同於「Bcan 沒有使用
bit 3」——不應為此新增 ROZ 分支，除非日後出現能讓兩個條件同時成立的具名遊戲路徑。

### 7.6 仍待硬體

Bcan 的 ROZ 解讀是否為硬體行為，需要在實機上以同一狀態切換 bit 3 並擷取
UM6618→UM70C188 的 `P0–P7`／`PCLK`，或比對同畫面 composite 輸出。在那之前，
`$F001F0` bit 3 在本庫維持 `unknown pixel mode bit 3`，不得命名為 TrueColor enable；
若要在模擬器實作，應標為 `confirmed-Bcan` 的相容性選擇。
