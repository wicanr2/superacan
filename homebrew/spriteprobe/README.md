# spriteprobe：UM6618 sprite 表欄位的量測卡帶

兩頁測試卡帶，每頁 24 筆 sprite 排成 4×6 網格，每格只差一個欄位值。用途是把
sprite 表的欄位語意從「反編譯讀出來的假設」變成「可重跑的量測」。

結論與公式寫在 [../../docs/sprite-format.md](../../docs/sprite-format.md)，
本檔只記怎麼跑、怎麼判讀。

## 版權邊界

映像的 `$2000–$23FF` 是卡帶授權區（1024 bytes，八款流通 ROM 完全相同），建置時由
**使用者自己的 ROM** 取出。產物 `build/*.bin` 因此含有版權資料：只留本機，不進版控。

## 建置與執行

```sh
python3 build.py --auth-rom "../../Bcan008b/ROMS/Boom Zoo (Taiwan).bin" --page 1
python3 build.py --auth-rom "../../Bcan008b/ROMS/Boom Zoo (Taiwan).bin" --page 2
```

建置時會印出每一格的欄位值與依公式算出的預期寬高，可直接與截圖比對。
Bcan 端的操作方式（不吃命令列 ROM 參數、要走 GUI）見 `../bit3probe/README.md`。

逐張截圖的判讀方式見 [../../docs/test-screenshots.md](../../docs/test-screenshots.md) §4。

## 判讀

sprite 圖形是**解碼圖**：像素值 ＝ `x + 8y + 64t`，調色盤把 `x` 編進紅、`y` 編進綠、
tile 編號 `t` 編進藍。所以截圖上每一個 sprite 像素都能反推它取樣自哪一張 tile 的哪一格：

```python
x = (r >> 3) // 4        # r、g、b 是截圖顏色，先還原成 5-bit
y = (g >> 3) // 4
t = (b >> 3) // 8
```

第一版探針用的是純白圖形，只量得到外接矩形——**尺寸全對，取樣卻整片錯**，
因為單色圖看不出 mosaic 正在把畫面切塊。要驗證取樣函式，測試圖必須讓每個來源像素可辨識。

## 兩頁掃了什麼

| 頁 | 列 | 掃描 |
|---|---|---|
| 1 | 0–1 | `hscale`（word2 bits 15–11）11 個值 |
| 1 | 2 | `vscale`（word0 bits 15–13）6 個值 |
| 1 | 3 | mosaic（word1 bits 5–3）6 個值 |
| 2 | 0 | 整體翻轉兩軸、tile entry 自帶的翻轉 |
| 2 | 1 | 翻轉與縮放並用，檢查兩者先後 |
| 2 | 2 | 2×2 子 tile 表，加翻轉與縮放 |
| 2 | 3 | ySize 索引 0–3，加翻轉與垂直縮放 |

2026-09-02 的結果：兩頁 48 個案例，Bcan 0.0.8b 與本專案 Linux 重製的畫面逐像素相同
（相異 0／76800）。
