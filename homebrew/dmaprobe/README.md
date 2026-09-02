# dmaprobe：主機 DMA control 位元的量測卡帶

一顆映像跑 12 個 control 值，把每次搬移的結果與搬完後的 DMA 暫存器都畫到畫面上，
因此「搬了幾個單位、往哪個方向、暫存器停在哪裡」全部可以從一張截圖逐 byte 讀出來。

結論寫在 [../../docs/host-dma.md](../../docs/host-dma.md)，本檔只記怎麼跑、怎麼判讀。

## 版權邊界

映像的 `$2000–$23FF` 是卡帶授權區（1024 bytes，八款流通 ROM 完全相同），建置時由
**使用者自己的 ROM** 取出。產物 `build/*.bin` 因此含有版權資料：只留本機，不進版控。

## 建置與執行

```sh
python3 build.py --auth-rom "../../Bcan008b/ROMS/Boom Zoo (Taiwan).bin"
python3 build.py --auth-rom "../../Bcan008b/ROMS/Boom Zoo (Taiwan).bin" --fault-case
```

`--fault-case` 會多加一個沒有觸發位元的非零 control。反編譯顯示 Bcan 對它回錯誤碼，
可能導致安全停機並讓整張截圖作廢，所以預設不含，要驗這條時單獨建一顆。
Bcan 端的操作方式見 `../bit3probe/README.md`。

## 版面

每個案例佔畫面上的一列（8 像素高）：

| 欄 | 內容 |
|---|---|
| 0–3 | 該案例的 256 byte 目的區。事前全部填成索引 255，所以「被搬到的 byte」一眼可辨 |
| 5 | 搬完後讀回的六個 DMA 暫存器（source 高低、dest 高低、count、control）|

目的位址從 256 byte 區塊的**正中央**開始，遞減方向才不會踩進隔壁案例。來源是 ROM 裡
64 byte 的斜坡（值 ＝ 索引 + 1），所以搬進來的每個 byte 都能對回它在來源的位置。

視訊在跑 DMA 之前就設定好：萬一某個 control 值讓模擬器安全停機，畫面上仍看得到停機前
已完成的案例，不會整輪作廢。

## 結果（2026-09-02）

12 個案例的**搬移結果**在 Bcan 0.0.8b 與本專案 Linux 重製上完全相同（逐 byte）。
唯一的差異是暫存器回讀：Bcan 一律回 0，本專案回推進後的實際值——Bcan 的讀取分派器
對 `$E90020–$E9003F` 沒有 case，屬未實作。詳見 host-dma.md §5。
