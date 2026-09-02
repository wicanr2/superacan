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
python3 build.py --auth-rom "../../Bcan008b/ROMS/Boom Zoo (Taiwan).bin" --channel 1
python3 build.py --auth-rom "../../Bcan008b/ROMS/Boom Zoo (Taiwan).bin" --independence
python3 build.py --auth-rom "../../Bcan008b/ROMS/Boom Zoo (Taiwan).bin" --extra-control 0x0001
python3 build.py --auth-rom "../../Bcan008b/ROMS/Boom Zoo (Taiwan).bin" --extra-control 0x8800
```

`--channel 1` 把整組案例改跑在 `$E90030`。因為目的區與案例都一樣，**兩張截圖應該逐像素
相同**——這個比對本身就是通道 1 的驗收條件，不必另外訂判準。

`--independence` 換成三個案例，驗兩個通道的暫存器檔是不是分開的：先把通道 1 設好但
control 寫 0，改用通道 0 搬一次，最後只寫通道 1 的 control。共用的話第三步會搬到通道 0
的目的區。

`--extra-control` 追加第 13 個案例。沒有觸發位元的非零值（如 `$0001`）會讓 Bcan 停止
整個工作階段、連截圖都產不出來，所以預設不含。**要把停機歸因給某個值，必須用合法值
（如 `$8800`）建同樣有 13 個案例的映像做正對照**——否則分不出是那個值造成的，
還是多一個案例本身讓版面出錯。Bcan 端的操作方式見 `../bit3probe/README.md`。

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
整張畫面的差異只有 168 個像素，全部落在暫存器回讀那一欄與它的 tilemap wrap 複本：
Bcan 一律回 0，本專案回推進後的實際值——Bcan 的讀取分派器對 `$E90020–$E9003F`
沒有 case，屬未實作。詳見 host-dma.md §5。

`--extra-control 0x0001` 的映像在 Bcan 上停止工作階段；同版面的 `0x8800` 正對照
跑完並正常截圖，因此停機可以歸因給那個 control 值本身。

`--channel 1` 的畫面與通道 0 的版本在兩個模擬器上各自都是 0 個像素差；`--independence`
的三列結果（16／8／0 個 byte）顯示兩個通道的暫存器檔是分開的，Bcan 與本專案相同。

**搬移要花多久沒有量到**，兩個模擬器都是觸發即完成。可查的參考與收斂方式見
[host-dma.md](../../docs/host-dma.md) §6。
