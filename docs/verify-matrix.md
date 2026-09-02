# 逐遊戲驗證矩陣

十二款正式軟體的目錄在 [software-catalog.md](software-catalog.md)；這一份記錄**本地九個
映像實際跑起來的樣子**：可重播的畫面檢查點、它們真正啟用了哪些硬體圖層，以及這份矩陣
涵蓋不到的範圍。量測由 [`tools/verify_matrix.py`](../tools/verify_matrix.py) 產生，
內容只有雜湊與布林值，不含任何 ROM 內容。

## 1. 涵蓋範圍

| | 數量 | 說明 |
|---|---:|---|
| 正式發售 | 12 | F001–F012，MAME snapshot 記「已知正式遊戲皆已 dump」 |
| 本地有映像 | 9 | 缺 **F009 賭霸、F010 魔棒撞球、F012 叛星** |
| 本矩陣涵蓋 | 9 | 含 F007 的 ZIP 容器 |
| 有正式驗證文件 | 3 | 其餘只有本表的開機路徑檢查點 |

**這份矩陣只走開機到待機的路徑**：全程不注入任何按鍵，所以進不了選單之後的畫面。
它能抓的是「開機流程或渲染出現回歸」，不能代表遊戲可玩。真正的可玩性驗證需要逐款的
玩家路徑腳本，那還沒有做。

## 2. 量測結果

| 映像 | steps | 非黑像素 | 音訊非零 | 曾致能的圖層 | 畫面檢查點 |
|---|---:|---:|---:|---|---|
| `Boom Zoo (Taiwan).bin` | 25625194 | 22556 | 656020 | normal layer 0、sprite、ROZ、window 0 | 76b4e20f c550d274 64a5caae e587bf15 7e1823f7 f69ec354 |
| `Formosa Duel (Taiwan).bin` | 28519581 | 76800 | 936322 | normal layer 0、sprite、ROZ、window 0 | 0870e23a 44e5b941 f991ee1a 5d641653 81e472e3 c69009d6 |
| `Journey to the Laugh (Taiwan).bin` | 26635798 | 0 | 1221637 | normal layer 0、sprite、ROZ、window 0 | 6db9bac8 878455a3 c1dc1f56 2e26ddce d43f1132 601280cd |
| `Monopoly - Adventure in Africa (Taiwan).bin` | 17114127 | 76800 | 1222012 | normal layer 0、normal layer 1、sprite、ROZ、window 0 | 04252f2f 601280cd ab01d4d7 15aa124a d33b769f a15904b5 |
| `Sango Fighter (Taiwan).bin` | 16437933 | 47228 | 1295744 | normal layer 0、normal layer 1、sprite、ROZ、window 0 | 225bab65 d8e80c5e 8a91ecac 27996fb9 039df9ff 72a4acac |
| `Speedy Dragon (Taiwan).bin` | 27851173 | 64341 | 1019605 | normal layer 0、normal layer 1、sprite、ROZ、window 0 | da964382 270eee3c aaf016a5 727c1c0a ae7346e4 75a5646d |
| `Super Dragon Force (Taiwan).zip` | 37106324 | 2500 | 1283041 | sprite、ROZ、window 0 | 601280cd 87f53b6d bffba601 1374aca9 640397e9 def9359a |
| `Super Taiwanese Baseball League (Taiwan).bin` | 26428535 | 45084 | 1116352 | normal layer 0、sprite、ROZ、window 0 | 601280cd 601280cd 02e53fc2 df36ccd8 b2f30434 435b78aa |
| `The Son of Evil (Taiwan).bin` | 25090352 | 20287 | 939233 | normal layer 0、normal layer 1、sprite、ROZ、window 0 | 601280cd f4a18d09 c159bd5b 60c907d9 07eca683 380b9d26 |

條件：每個映像 1800 幀，每 300 幀取一次畫面，檢查點是該 PNG 的 SHA-256 前 8 碼。
`601280cd` 是全黑畫面（嘻遊記的末幀非黑像素為 0，末檢查點正是這個值）。

## 3. 從致能位元看硬體用量

「曾致能的圖層」取自 `$F00008` 所有寫入值的聯集，不是看功能暫存器有沒有被寫——
**寫入不等於啟用**。實測：

| 硬體功能 | 致能位元 | 有幾款啟用 |
|---|---|---:|
| normal layer 0 | bit 7 | 8／9 |
| normal layer 1 | bit 6 | 4／9 |
| normal layer 2 | bit 5 | **0／9** |
| normal layer 3 | bit 4 | **0／9** |
| sprite | bit 3 | 9／9 |
| ROZ | bit 2 | 9／9 |
| window 0 | bit 1 | 9／9 |
| window 1 | bit 0 | **0／9** |

三個從來沒被啟用的功能各有不同意義：

- **normal layer 2**：本專案與 Bcan 都有實作，但沒有本地軟體用它。屬「實作了但未經
  軟體驗證」，不是缺口。
- **normal layer 3**：本專案與 Bcan 都**沒有**實作。F005 與 F003 會寫 `$F00160–$F0017F`，
  但寫進去的值全是 `$0000`（初始化清空）。既沒有 oracle 也沒有 consumer，維持 `unknown`。
- **window 1**：本專案有對稱實作、Bcan 沒有（renderer 不讀 snapshot 的 `+172` 欄位）。
  四款會寫它的暫存器但都沒啟用。同樣維持假說。

## 4. 量測方法上的坑

`--watch` 只保留前 64 筆事件。同時盯多個位址區段時，最吵的那一段會把其他段擠掉，
於是得到「看起來沒用到」的**假陰性**——第一版的功能欄就是這樣把四款有寫 window 1
暫存器的遊戲全報成「只有 window 0」。判斷功能有沒有被啟用要看致能位元，
`$F00008` 的寫入很稀疏，不會觸發這個上限。

## 5. 重跑

```sh
python3 tools/verify_matrix.py --emu <acan-headless 路徑> --bios <bios 目錄> \
    --roms Bcan008b/ROMS --frames 1800 --every 300
```

模擬器與 BIOS 都是本機研究輸入，路徑由呼叫端給。檢查點會隨模擬器實作改變而改變——
那正是它的用途：改動渲染後重跑，比對哪一款、哪一個時間點變了。

## 6. 還缺什麼

1. **逐款玩家路徑腳本**。目前九款都只驗到待機畫面。至少要能「進入遊戲主畫面」才算
   有意義的相容性宣告。
2. **F009／F010／F012 沒有本地映像**，矩陣結構上就有三個洞，不能宣稱十二款皆已驗證。
3. **F007 在 1800 幀內沒有啟用任何 normal layer**，非黑像素只有 2500，可能還停在開機
   段落。需要更長的執行或按鍵才判斷得出來。
4. **與 Bcan 的逐像素對拍還沒做在商業 ROM 上**。目前只有自製卡帶做過（相異 0），
   商業 ROM 的差分需要先對齊兩邊的取樣時機。
