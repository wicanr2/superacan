# 工作歷程

## 2026-09-02：三個子系統的探針補完（sprite mask、mosaic、主機 DMA）

- **sprite mask 模式不是繪製當下判斷，是整幀後處理。** spriteprobe 第 3 頁（16 種 A×B
  組合）量到第 6、7 格 Bcan 有畫、本專案沒畫：寫遮罩的 sprite 排在被遮罩的後面時，
  Bcan 仍然畫得出來。反編譯 `sub_14009D6E0` 對上了——每像素有一個旗標 byte 與一份
  被蓋掉的顏色備份，全部畫完才結算。
- **整幀沒有任何遮罩時，mask=1 轉成半透明。** 底下有 sprite 就把兩者的**調色盤索引
  相加**，只有背景就逐通道取平均。加第 4 頁探針專測這條分支，八格逐像素相符；
  負對照（當成不透明／一律丟棄）分別差 446、445 個像素。
- **mosaic 是查表，不是位元遮罩。** `.rdata` 的 `unk_140423508` 有九張 320 項表，
  第 k 張是 `floor(d/k)×k`，欄位值 m 取第 m+1 張——塊大小是 `m + 1`。新增
  `homebrew/mosaicprobe/`，一般圖層與 ROZ 各兩個值，四顆映像查表模型差 0，
  位元遮罩模型差 5.76 萬–7.64 萬。ROZ 先前完全沒實作 mosaic。
- **主機 DMA control 位元全部量完。** 反編譯 `sub_1400A31A0` 讀出觸發條件
  （`& $8800`）、`count + 1` 單位、±1／±2 步進、`bit8` 的退 16 規則、`$A800` 的相等比對
  特例、以及「非零但沒有觸發位元 → 回錯誤碼且不寫入暫存器」。新增
  `homebrew/dmaprobe/` 12 個案例逐 byte 驗證，搬移結果與 Bcan 完全相同。
- **非零但沒有觸發位元的 control 會讓 Bcan 停止整個工作階段**（回錯誤碼 12）：同版面把
  最後一個案例換成合法的 `$8800` 做正對照，前者跑完照常截圖，後者連 F8 都產不出檔案，
  而且沒有留下 `*.fault.txt`。本專案的重製不停機，只是不觸發搬移。
- 新文件：[docs/tilemap-format.md](docs/tilemap-format.md)、[docs/host-dma.md](docs/host-dma.md)；
  [docs/sprite-format.md](docs/sprite-format.md) 增 §5 mask 與半透明。
- 驗證矩陣重跑：九款映像 54 個檢查點，mosaic 修正前後**逐字相同**；sprite mask 修正
  只動了非洲探險的第 3 個檢查點——那一格的顏色變暗，代表它真的用 mask=1 當半透明。
  這是本地軟體第一次被量到使用這個功能。

- **sprite mask／整幀結算結案**：欄位語意、兩條結算路徑、半透明公式都已定案並實作，
  87 個案例逐像素相符。唯一殘留的是掃描範圍（Bcan 掃視窗矩形、本專案掃整個畫面），
  已寫進 sprite-format.md §5.1 並**接受為現況**，不列待辦——判它需要實機或新的軟體
  案例，兩者都不在現有手段內。

### 這一輪的方法教訓

- **解碼圖的反查表要排除背景色。** 第 3 頁一度被判成「16 格全相同」，因為調色盤索引 0
  同時是 backdrop 與 tile 0 的第一個像素，整片背景被讀成「tile 0 到處都在」。
- **「差 0 個像素」單獨沒有意義。** 每次下相符的結論都要同時算競爭模型差幾個，
  才知道那個 0 不是恆真。這一輪四個結論都附了負對照。
- **被工具逾時砍掉的 `docker run` 客戶端會把容器輸出丟掉**，容器本身還在跑。
  長工作要嘛背景執行，要嘛把輸出寫進掛載目錄，不能只靠客戶端的 stdout 轉向。
- **DMA 探針把視訊設定排在觸發之前**：某個 control 值若讓模擬器安全停機，
  畫面上仍看得到停機前完成的案例。這是 soundregprobe 整輪作廢換來的順序。
  實測 Bcan 的停機更徹底——直接回到未載入 ROM 的狀態，什麼都留不下，
  所以歸因只能靠「同版面換一個合法值」的正對照，不能靠畫面殘留。

## 2026-09-02：UM6619 埠協定的反編譯補證，與一個可列舉暫存器的手段

- 反編譯 Bcan 的 65C02 匯流排讀寫端（`sub_1400A59C0`／`sub_1400A5220`）：
  - 寫 `$0420` 只把暫存器編號閂進內部欄位，寫 `$0422` 才送出編號＋資料。
  - **寫一個 ≤ `$3F` 的值進暫存器 `$14` 也會 ack timer IRQ**，不是只有讀取會。
  - 送出前先查該編號是不是 Bcan 已知的暫存器；不認得的不丟棄，而是記進故障報告
    （`*.fault.txt`）。
- 後者給了一個現成手段：寫一顆把 `$00–$FF` 全掃一遍的 65C02 驅動，Bcan 的故障報告
  會直接列出它沒有實作哪些暫存器，`$40–$4E`／`$A0–$DF` 的待查證可以這樣收斂。**尚未執行。**
- UM6619 的實際暫存器語意（envelope 等）在 audio 物件的 vtable 後面，這一輪沒有追進去。

## 2026-09-02：計數器（`$E90014/16/18`）的週期公式定案

- 反編譯 Bcan 的 `$E9xxxx` 寫入分派器（`sub_1400A2C10`）找到 `$E90014` → `sub_1400A7420`、
  `$E90016` → `sub_1400A7510`，兩者算同一件事。公式與換算見
  [docs/memory-map.md](docs/memory-map.md) §2.2。
- 關鍵是三個魔術常數拆得開：`0x199A57B800 = 1024 × 107386350`、
  `0xE2068E6460 = 9040 × 107386350`、`8948862 = ⌊107386350/12⌋`。master 約掉之後
  剩下純 tick 數，於是**計數器的輸入時脈是 master/12 = 8.9488625 MHz**。
- 模式由 control 低 4 bit 選：`$0` 固定一秒（與週期無關）、`$1` 每 1024×(n+1) 輸入 tick、
  `$F` 每 9040×(n+1)。高位元組必須是 `$A2`。
- 本地實測**沒有遊戲用過 `$1` 或 `$F`**：Speedy Dragon 只用 `$A200`（每秒一次），
  與它 IRQ3 handler 累加 `$FCE00E` 的計時器語意吻合；Formosa Duel 寫 `$A000` 是停用。
  先前把 Speedy 的「設週期→啟動」當成校準入口，其實那個週期值在模式 `$0` 下無效。
- `../superacan-emu` 的 `chip/frc` 依此改寫：改記主時脈 tick、週期算 `(n+1)`、倍率改成
  12×1024 與 12×9040。原本是 MAME 衍生的 `1024×n`／`8192×n` 且以 68k cycle 計。
  兩款會碰計數器的遊戲改前改後畫面相同——因為它們用的都是模式 `$0`，那條路徑兩邊等價。
- 絕對單位仍是強推論：要釘死得看 Bcan 排程器怎麼消費 `counter+32`，或在實機上量。

## 2026-09-02：`$F001F0` bit 4 定案，pixel mode 四個位元全部有結論

- 新增 `homebrew/pixelmodeprobe/`：同一個 ROZ 8bpp 場景，每 300 幀把 `$F001F0` 換成
  `$02`／`$0A`／`$12`／`$1A`，量 bit 4 做不做事。
- 結果：**只有 pixel mode 恰為 `$08` 會走 bitmap 路徑**。`$10` 與 `$18` 都回到 tilemap，
  所以 bit 4 沒有獨立效果，只是 bit 3 的排他條件。Bcan 與本專案產生的四張畫面完全相同。
- 至此 `$F001F0` 四個欄位都有定論：bits 0–2 gfx mode（同 MAME）、bit 3 ROZ 的
  tilemap／bitmap 切換、bit 4 只作排他條件。direct-color 假說再被削弱一層
  （docs/palette-dac.md）。
- 探針設計上的一點：**相位標示要挑「在所有相位都看得見」的位置**。第一版只改 backdrop
  （調色盤索引 0），但 ROZ 蓋滿整個畫面時 backdrop 一個像素都沒露出來，四個相位分不開。
  改成同時寫索引 0 與索引 255（地圖中央的標示方塊）才量得出來。

## 2026-09-02：驗證矩陣，以及第四層／window 1 的斷言訂正

- 新增 [`tools/verify_matrix.py`](tools/verify_matrix.py) 與
  [`docs/verify-matrix.md`](docs/verify-matrix.md)：本地九個映像各 1800 幀，
  每 300 幀一個畫面檢查點，加上「曾致能哪些圖層」。
- **訂正一個我自己當天稍早推送出去的錯誤斷言。** 先前寫「F005 與 F003 會寫滿第四層的
  整個暫存器區塊，因此少畫一層在跑」「window 1 已有四款具名 consumer」。實際量測：
  - 九款都沒有把 `$F00008` 的 **bit 4（第四層）或 bit 0（window 1）** 設起來。
  - F005／F003 寫進第四層區塊的值**全是 `$0000`**，是初始化清空。
  - Bcan 也沒有實作這兩者：snapshot 只有三組 tilemap 欄位、renderer 圖層迴圈只跑三次，
    window 1 的 snapshot 欄位 `+172` 一次都沒被讀。
  - 順帶量到 **normal layer 2 也從未被啟用**（實作了但沒有軟體驗證過）。
  教訓：**「有寫這個暫存器」不等於「有用這個功能」。** 判斷功能是否啟用要看致能位元。
- 量測方法的坑：`--watch` 只保留前 64 筆事件，同時盯多個區段會被最吵的那段淹掉，
  產生「看起來沒用到」的假陰性。第一版功能欄就是這樣把四款有寫 window 1 暫存器的
  遊戲全報成只有 window 0。
- `../superacan-emu` 一併修正 window 1 的致能位元（`flags&2` → `flags&1`，Bcan 的
  snapshot builder 為 `+160←v2&2`、`+170←v2&1`）。四款會寫 window 1 暫存器的遊戲
  改前改後畫面完全相同，是純正確性修正。

## 2026-09-02：rich2demo 補上可重跑的部分與可進版控的截圖

- **匯出程式入庫**（`homebrew/rich2demo/export/main.go`）。先前它只存在暫存目錄，
  重現鏈實際上是斷的：README 只寫「以 rich2 模組內的一支小程式呼叫 ParseBoard…」，
  沒有人能照著跑出同一份素材。
- **`manifest.json`**：記下原版輸入（`PART1.PAK`／`256.PAT`／`SAVE_2.DSK`／授權來源 ROM）、
  匯出素材、中間產物與卡帶映像的 SHA-256。`build.py` 建置後自動核對，不符以非零離開；
  `--write-manifest` 改記錄。版權檔案不進版控，雜湊可以——拿自己的合法原版重跑能直接
  確認位元相同。
- **`--art placeholder`**：131 種地形各配一色加一圈格線，調色盤與圖塊都由 `build.py`
  生成。棋盤版面仍是原版道路網（同地形連成色塊，道路與街廓的分佈讀得出來），但畫面
  沒有任何一個像素來自原版美術，因此截圖可以進版控並放進 README。
  第一版配色彩度太高，整張圖變成看不出結構的彩色雜訊，往中灰混一半才讀得出區塊。
- 佔位模式的初始畫面與 Bcan 0.0.8b 跑同一顆映像逐像素相同（相異 0／76,800），
  所以這張截圖本身是經過 oracle 驗證的，不只是「我方畫出來的樣子」。
- `--art original` 的產物與截圖維持只留本機，與 `~/cht/rich2/.gitignore` 的既有政策一致。

## 2026-09-02：測試截圖獨立成章

- 新增 [docs/test-screenshots.md](docs/test-screenshots.md)：三顆自製卡帶的截圖各自在證明
  什麼、怎麼產生、該看哪裡、量到什麼數字，集中一處，homebrew 的三份 README 改成指過去。
- `assets/screenshots/` 只收畫面內容完全由自製卡帶生成的圖（bit3probe 兩個相位、
  spriteprobe 兩頁），並記錄像素 SHA-256。四張的像素內容與本專案輸出逐像素相同；
  檔案位元組不同只是兩邊 PNG 編碼器的差異。
- **rich2demo 的截圖不進版控**：那些畫面是《大富翁2》的原版地圖圖磚與調色盤。該節改以
  自繪的 `rich2demo-layout.svg`（視窗位置、11×11 網格、24×20 如何排成 8×8 tile）
  加上對拍數字承載結論，並附本機重現步驟。
- 另收三個判讀截圖時踩過的坑：單色測試圖藏住取樣錯誤、狀態標示與空畫面同色、
  位移類假說用直方圖判斷。

## 2026-09-02：sprite 表的縮放與 mosaic 欄位定案

- 起因是 rich2demo 記下的分歧：同一筆 sprite 表項目，本專案畫 8×8，Bcan 畫成約 40×6 的
  橫條。反編譯 Bcan 的 sprite 迴圈後看出成因——我們當成「保留位元＋致能位元」的欄位，
  其實是縮放：
  - `word2` bits 15–11 是水平縮放，`width = (hscale + 6×nw) / (hscale + 1)`，1:1 的值是 5。
  - `word0` bits 15–13 是垂直縮放，`height = vscale ? (vscale + 2×nh − 1)/vscale : 3×nh`，
    1:1 的值是 2。我們原本把 bit14 當致能位元，那其實只是 `vscale = 2` 的一個位元。
  - `word1` bits 5–3 是 mosaic，塊大小 = 值 + 1。
- 量測用 `homebrew/spriteprobe/`：兩頁卡帶各 24 筆 sprite 排成 4×6，每格只差一個欄位值。
  第一版探針的 sprite 圖形是純白，**外接矩形 24／24 全中，取樣卻整片是錯的**——單色圖
  看不出 mosaic 正在把畫面切塊。改成「像素值 = x + 8y + 64t、調色盤把座標編進 RGB」的
  解碼圖之後，截圖上每個像素都能反推來源座標，取樣函式才量得出來：
  `src = (dst / m × m) × native / drawn`，塊原點是 `floor(d/m)×m`，**不是位元遮罩**
  （量到 m = 3 與 6 都成立，位元遮罩在這兩個值會錯）。
- 實作進 `../superacan-emu` 後，兩頁 48 個案例與 Bcan 逐像素相同（相異 0／76800），
  涵蓋縮放、mosaic、整體翻轉、tile entry 翻轉、2×2 子 tile 表與 ySize 索引。
- 回歸驗證：本地五款 ROM 各 1500 幀、每 150 幀取樣，共 30 個檢查點，改動前後完全相同。
  已發行軟體在這些段落用的都是 1:1 且 mosaic 0，縮放與 mosaic 是有硬體、軟體沒用到的能力。
- 結論寫入 [docs/sprite-format.md](docs/sprite-format.md)。證據等級 `confirmed-Bcan`，
  硬體真相仍待實機訊號。

## 2026-09-01：大富翁2 台灣棋盤的自製 demo 卡帶

- 新增 `homebrew/rich2demo/`：1 MiB 自製卡帶，以原版 11×11 視窗顯示台灣棋盤，按 A 擲骰、
  棋子沿鄰接表移動，岔路可用方向鍵指定、一秒沒指定就隨機（原版本來就是隨機抽）。
- 素材路徑：`~/cht/rich2` 的 `internal/assets` 已能解析棋盤（區段 3）、36×36 地圖圖層
  （區段 4／5）、131 張 24×20 圖磚（`PART1.PAK` 區段 0）與 `256.PAT` 調色盤。因為
  `internal` 套件不能跨模組 import，做法是把 `go.mod`／`go.sum`／`internal` 複製成一份
  暫時模組再加一支 `cmd/dump`。三種版權輸入都在建置時取自本機檔案，產物不進版控。
- 畫面：A'Can 的 tile 是 8×8、原版圖磚是 24×20，高度不整除。解法是把 11×11 格攤成
  264×220，寫進 VRAM 時就排成 8×8 packed 8bpp 的 924 張 tile，tilemap 用線性索引指過去。
  24 是 8 的倍數，所以來源每列正好落在三張相鄰 tile 的同一列，搬移是「三段 8 bytes、
  間隔 64」，整個視窗約 14,520 個 `move.l`。
- 正確性佐證：初始畫面與 rich2 的 `RenderMapViewport` 逐像素相同（扣掉棋子的 32 px，
  且需先把參考圖做 5-bit 量化，因為 A'Can 調色盤是 xBGR555）；本專案模擬器與 Bcan 的
  初始畫面相異 0／76800。
- 兩個實測差異：
  1. **手把必須由 65C02 掃描**。`$0407` 的 latch／shift 與 `$0402` 只有 65C02 摸得到，
     68k 讀的是 65C02 寫進 sound RAM `$0200` 的值。本專案模擬器在 68k 讀 `$E80200` 時
     直接合成宿主輸入，因此少了驅動也能動；Bcan 不合成，沒驅動就毫無反應。ROM 因此
     自帶 41 bytes 的 65C02 掃描迴圈。**輸入路徑是否真的正確，要以 Bcan 為準。**
  2. **sprite 表的解讀有分歧**。同一筆 `w0=$4000 w1=$4000 w2=x w3=$8000` 在本專案畫出
     8×8 一張圖，在 Bcan 畫成約 40×6 的橫條。demo 改成把棋子蓋進 tile 版面後兩邊一致，
     但欄位語意的分歧尚未查清楚，是下一個值得追的題目。
- 過程踩到的坑：`wait_frame` 用了 `%d0` 當暫存，呼叫端的延遲計數器因此被蓋掉，
  10 幀的等待變成三萬多幀，看起來就像整個程式當掉。**子程式要嘛不留副作用，
  要嘛把破壞的暫存器寫在介面上。**

## 2026-09-01：自製 bit3 測試卡帶，解出 `$F001F0` bit 3 的語意

- 新增 `homebrew/bit3probe/`：68k 組語原始碼與建置腳本，產出 512 KiB 卡帶映像。
  ROZ 設為 8bpp region、identity 變換，主迴圈每 300 幀切換 `$F001F0`（`$0001`／`$0009`），
  backdrop 在兩個相位分別為紅／綠以自證相位。工具鏈為 Debian `binutils-m68k-linux-gnu`
  容器（`acan-m68k:bookworm-v1`）。
- 開機關卡：卡帶授權區實測為 `$2000–$23FF` 共 **1024 bytes**，八款流通 ROM 完全相同；
  建置時由本機 ROM 取出注入，映像因此能通過 IPL 的兩階段檢查。產物含版權資料，
  只留本機、不進版控。
- 結論：bit 3 是 ROZ 層的 **tilemap／bitmap 切換**。bit 3 = 1 且 ROZ 為 8bpp region 時，
  Bcan 跳過 tilemap 與 tile 圖形，以 `4 × $F00196` 為 byte 基底、`0x1FFFF` 為遮罩逐像素
  線性讀 VRAM。基底倍率由 `$F00196` 對照實驗定位（條紋由第 32–39 列移到第 0–7 列）。
- 過程勘誤（正文已改為結論版，此處保留推翻紀錄）：
  1. 第一版探針的 backdrop 與 bit3=0 的相位標示同為藍色，兩個相位分不開，一度把
     「bit 3 = 1 時整層空白」記成「bit 3 = 0 時整層空白」。改成兩個相位不同底色後推翻。
     教訓：**用來標示狀態的顏色不能與「什麼都沒畫」的顏色相同**。
  2. 空白的成因也記錯過。填滿 VRAM、讓視窗內沒有零 byte 之後才確定：空白不是「整層
     未繪製」，而是 bitmap 路徑讀到全零的 VRAM 區段。
  3. `$F00196` 對照實驗一度被判為「沒有變化」，因為只比對顏色直方圖——兩張圖的內容
     相同、只是位移，直方圖幾乎一樣。改看條紋所在列才看出差異。
     教訓：**位移類假說要用位置量測驗證，不能用整體統計量。**
- `../superacan-emu` 依此實作 bitmap 路徑（`rozBitmapPixel()`），同一顆卡帶兩個相位與
  Bcan 截圖逐像素相同（相異 0／76800）；一併移除該 renderer 多餘的 ROZ 整層翻轉。
- Bcan 操作紀錄：不接受命令列 ROM 參數，必須以 xdotool 走 `檔案(F)` → 第一項 → 輸入
  `Z:\work\bcan\ROMS\<檔名>`；容器內 wine 執行檔在 `/usr/lib/wine/wine64`，且要以
  與 wineprefix 相同的 UID 執行。

## 2026-09-01：ROZ bit 3 分支的可達性量測

- 背景：靜態反組譯確認 Bcan 有 pixel-mode bit 3 的 consumer；另一工作階段則得到「Bcan 沒有
  使用」的結論。兩者的差別在於「程式碼存在」與「執行期會不會走到」。
- 量測：在模擬器加純記錄探針，統計每幀 `(reg$1F0 & 0x18) == 0x08`、ROZ 致能、
  `(roz_mode & 3) == 3` 三者是否同時成立。八款本地 ROM 各 1200 幀，全部為 0；
  The Son of Evil 是唯一會進 ROZ 8bpp 的（1200 幀中 759 幀），延長到 6000 幀後
  `pixel bit 3 = 317`、`ROZ 8bpp = 4274`、同時成立仍為 0。
- 結論：兩層分述——Bcan 程式碼有該 consumer（指令佐證見 f003-video-mode.md §7.3），
  但在已知軟體路徑上從未執行，實作上等同沒有使用，不新增該分支。
- 副產品：八款 ROM 開頭都有約 191 幀 `pixel mode == $08`，該期間 ROZ 為 1bpp，
  對應共用的 A'Can 開機 logo；bit 3 與 8bpp ROZ 在時間上互斥。

## 2026-09-01：`$F001F0` 在 Bcan 的資料流解出，pixel mode 契約改寫

- 結果：pixel mode 與 gfx mode 都會進入 Bcan 每幀的 renderer snapshot（`+190`／`+191`），
  各有唯一讀取點。gfx mode 走與 MAME 相同的三張圖層 region 表換算色深；**bit 3 只在 ROZ
  層生效**——`pixel_mode == $08` 且 ROZ 為 8bpp region 時，改走 24-bit 逐行取值、不加全域
  ROZ scroll 基底，並多一次以 ROZ tile bank 為基底的 VRAM 遮罩查表。MAME 完全不消費
  pixel mode，故該路徑是 Bcan 獨有，等級 `confirmed-Bcan`。
- 因此前一輪「pixel mode 不進入 renderer」與「Bcan 不使用全域 gfx mode」兩項敘述均已作廢，
  f003-video-mode.md §7 改寫為逐指令佐證的資料流，palette-dac.md 的假說段落同步調整：
  唯一實作它的程式把 bit 3 當 ROZ 模式，而不是全域 direct color。
- 新增 [docs/re-method-decompiler-dataflow.md](docs/re-method-decompiler-dataflow.md)：
  記錄本輪三次「自洽但錯」結論的成因（掃描範圍與存取形式不匹配、把 Hex-Rays `HIWORD`
  當固定 byte lane、把含 `bp` 的運算元當堆疊過濾掉）與可重用的檢查清單。
- 工具：`ida-pro-9.4-idapython:locked-v1` headless，`idat -A -S`；分析副本用完刪除。

## 2026-09-01：兩項實作契約定案（跟隨 Bcan）

- 決定：sound RAM 採 **64 KiB 平面、不遮罩 A15**；`$F001F0` 的 pixel mode 解碼後只供
  讀回與存檔、**不進入 renderer**。兩項等級為 `confirmed-Bcan`，不是 `confirmed-hardware`；
  硬體側的未決狀態與可否證條件維持記錄在 memory-map.md §5.1 與 f003-video-mode.md §7。
- 現況核對：`superacan-emu` 的 `machine.Bus` 預設遮罩為 `0xffff`、`chip/umc6618` 的
  renderer 不使用 bit 3／bit 4，已符合契約，無須改碼；32 KiB alias 開關維持診斷用途。
  該專案另新增 `docs/sound-ram-model.md` 記錄同一決定。
- 新開放問題：Bcan 的 renderer snapshot 不含全域 gfx mode，代表它以逐圖層暫存器決定
  色深與 tile region；本專案文件與 superacan-emu 目前採 MAME 的全域規則。兩者不同，
  應以 Sango Fighter（`$F001F0 ← $0003`）做同畫面差分釐清，未釐清前不動現行規則。

## 2026-09-01：Bcan 反編譯確認 sound RAM 模型與 pixel-mode 消費者

- 工具：IDA Pro 9.4（`ida-pro-9.4-idapython:locked-v1`，headless `idat -A -S`，Hex-Rays），
  對本機 `Bcan008b/Bcan.exe.i64` 只讀分析；分析副本用完刪除。
- **sound RAM**：65C02 側 `sub_1400A59C0`（讀）／`sub_1400A5220`（寫）以完整 16-bit 位址
  `switch`，`$0400–$04FF` 逐一列為 I/O case，其餘 `default:` 走
  `*(BYTE *)(*(QWORD *)(obj+16) + a2)`——未遮罩索引同一塊緩衝區。68k 側
  `SystemBus` 判斷 `(addr & $FF0000) == $E80000` 後轉發完整位址；分類器保留
  `addr − $E80000`。存檔機器區段（`ACMS`）序列化 `0x10000`／`0x10000`／`0x8000` 三塊。
  結論：Bcan 假設 64 KiB、無 A15 alias，寫入 memory-map.md §5.1。
- **pixel mode**：Bcan 每幀由 `sub_140082130` 建 snapshot 給 renderer `sub_14009D6E0`
  （輸入含 VRAM `0x20000`、palette 256、輸出 76800 像素）。建構器以
  `mov rax,[rdx+29324h]` 一次取 `video+588..595`，只用低 4 byte（video flags 與各層致能
  位元）；byte 6（pixel mode）與 byte 7（gfx mode）未進入 snapshot。因此 Bcan 的 renderer
  結構上不依賴 `$F001F0`；附帶發現 Bcan 也不使用全域 gfx mode，色深改由各層 mode 暫存器
  決定，與 MAME 的 `get_tilemap_region()` 不同。
- 方法教訓：上一輪只掃「直接結構位移」就下 renderer 不消費的結論，正對照（tilemap base
  等必用欄位同樣掃不到）顯示該方法看不見 snapshot 路徑。這次改以
  screenshot 字串 → `sub_140048500` → `sub_140048E40` → snapshot 建構器 → renderer
  的呼叫鏈逐段確認，f003-video-mode.md §7 已改寫為此證據鏈。

## 2026-09-01：三個未定案項目的補證

- 目標：依序處理 sound RAM 32／64 KiB、`$E90014/16` 的兩套解讀、F003 pixel-mode bit 3。

### 1. sound RAM alias（部分定案）

- 靜態：以 word-swap 還原映像掃 `$00E8xxxx`，把上下半區依 mod 0x8000 對撞，候選全部落在
  圖形／指標資料，指令層只有高半區的 `lea $E8F000`；靜態不足以判別。
- 動態：在 superacan-emu 加入 `--sound-ram-alias` 診斷模式與對撞偵測後，四款 ROM 各 1200 幀
  A/B。兩種模型的指令數、VRAM、framebuffer 與 IRQ ack 完全相同；唯一差異是 Boom Zoo 音訊
  約 0.01% 樣本，對撞只有 `$040A/$040B`（mailbox 旗標 vs `$8400` 歌曲位址表）。
- 結論寫入 memory-map.md §5.1：現有路徑分不出兩種模型，唯一可量測分歧點已具名。

### 2. `$E90014/$E90016/$E90018`（定案）

- 以 Capstone 反組譯四個寫入點與其上下文、卡帶 autovector 表與 `$E90018` 的 consumer。
- Speedy Dragon：`$30CE` 設週期、`$30D4` 啟動、IRQ3 向量 `$3454` 做 `addq.b #1,$FCE00E`，
  `$30DE` 是等待該 tick 的迴圈——計時器語意在軟體層閉合。
- Formosa Duel：`$5EB4/$5EBC` 寫 `$A000`／`$FFFF`，在 `$6076/$607E` 連讀兩次 `$E90018` 拼
  32-bit 當種子，在 `$868A/$8696` 把讀值加到 `$F00124/$F00126`（tilemap 1 scroll），與 MAME
  「formduel 用它捲動雨層」的註解對上。
- Journey：`$FC6AC/$FC6B4` 設週期 `$8FC`＋control `$A0D6`，接著開 `$E90010=$C0C0` 並降 SR。
- 結論：三個位址是同一個計數器（控制／週期／目前值），到期拉 IRQ3；Bcan 的 DMA 位址與
  取樣播放位置命名是同一顆計數器的別名。真實週期公式仍未知，Speedy 的設週期＋等待迴圈
  是最好的校準入口。

### 3. F003 pixel-mode bit 3（判定為軟體 oracle 無解）

- 用 emu repo 的 Bcan oracle 管線跑 The Son of Evil，2 分鐘 20 張截圖，相異顏色數最高 118，
  全部遠低於 256。
- 為判斷這個否定結果是否有意義，以 IDA Pro 9.4（`ida-pro-9.4-idapython:locked-v1`）對
  `Bcan.exe.i64` 實測：`$F001F0` 的寫入在 `sub_1400A9200` 拆成 `& 0x18`／`& 7` 兩個 byte
  欄位（video+594／+595），而整個 `.text` 對這兩欄位的直接存取只有解碼、狀態一致性驗證器
  `sub_1400A96E0` 與存檔序列化 `sub_1400AAC80`；286 KB 的 renderer 不讀它們。MAME 同理。
- 結論寫入 f003-video-mode.md §7 與 palette-dac.md §5：沒有可用的軟體 oracle，下一步只剩
  實機 `P0–P7`／`PCLK` 擷取或 composite 量測。
- 方法限制已標明：掃描只涵蓋直接結構位移，未追指標間接路徑。

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
