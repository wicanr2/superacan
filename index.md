---
title: Super A'Can 硬體與逆向工程記錄
description: 1995 年台灣自製 16 位元家用主機的硬體規格、BIOS 反組譯、模擬器逆向與可重跑量測。
---

Super A'Can 是敦煌科技（Funtech，聯華電子子公司）在 1995 年推出的 16 位元家用主機，
主 CPU 為 MC68HC000P10、音效端另掛一顆 WDC 65C02，繪圖與音訊各由 UMC 自製的
UM6618、UM6619 負責。它只發行了十二款遊戲就退場，沒有留下任何原廠技術文件。
{: .lede }

這裡記錄的是把它一項一項量回來的過程：從 BIOS 開機流程、記憶體映射、繪圖晶片的欄位語意，
到音訊晶片的包絡產生器。每條結論都標註證據等級——**(a)** 模擬器或 BIOS 實測、
**(b)** MAME driver、**(c)** 二手報導、**(p)** 實機照片與板級電路。
互相矛盾時以 (a) 為準並記錄差異；查不到的寫「待查證」，不用類似主機的經驗填補。

其中一部分結論是靠**自製卡帶**量出來的：商業 ROM 從來不讓某些硬體狀態成立，
所以另外寫了幾顆測試卡帶去製造那些狀態，再拿同一份映像在模擬器上逐像素比對。

## 硬體

<div class="docs" markdown="1">

- [記憶體映射與硬體暫存器](docs/memory-map.md)
  <span class="note">68k 與 65C02 兩側的位址空間、UM6618／UM6619 暫存器、中斷與計數器。</span>
- [VRAM 實體架構與 128 KiB 視窗](docs/vram-architecture.md)
  <span class="note">板級裝片與 CPU 可見視窗的落差，以及 `VRAM_A17` 的接法。</span>
- [硬體證據的取得方式與界線](docs/hardware-evidence-method.md)
  <span class="note">哪些機制可由電路圖直接確認，哪些必須靠實測，以及不能從其他主機類推的部分。</span>
- [硬體組成與逐晶片模擬實作參考](docs/hardware-implementation-sources.md)
  <span class="note">固定來源 commit、PCB revision 差異、各晶片可參考的核心與已知缺口。</span>
- [逐晶片模擬實作指南](docs/chip-emulation-guide.md)
  <span class="note">實作順序、每顆晶片的最小契約，以及會讓遊戲鎖死的幾個細節。</span>
- [UM70C188 調色盤與 RAMDAC](docs/palette-dac.md)
  <span class="note">類比輸出級的型號考據與尚未證實的部分。</span>

</div>

## 開機流程與軟體格式

<div class="docs" markdown="1">

- [68k IPL 分析](docs/bios-68k.md)
  <span class="note">UMC6650 交握、卡帶授權區比對、overlay 關閉與跳轉入口。</span>
- [BIOS 完整控制流程與中斷向量](docs/bios-control-flow.md)
- [65C02 端 BIOS 取樣資料與開機流程](docs/bios-65c02.md)
  <span class="note">兩塊「6502 bin」其實是取樣資料，不是韌體。</span>
- [BIOS 與 ROM 格式](docs/bios-rom-format.md)
  <span class="note">無外加標頭、16-bit word-swap 的向量表、無 mapper。</span>
- [正式軟體目錄與本地 ROM 對照](docs/software-catalog.md)
  <span class="note">F001–F012 十二款的發行商、年份與雜湊台帳。</span>

</div>

## 繪圖

<div class="docs" markdown="1">

- [UM6618 sprite 表格式](docs/sprite-format.md)
  <span class="note">縮放、mosaic、翻轉、mask 模式與半透明。mask 是整幀後處理，不是繪製當下判斷。</span>
- [一般圖層與 ROZ 的 mosaic](docs/tilemap-format.md)
  <span class="note">塊大小是欄位值 +1 的查表，不是 2 的冪次位元遮罩。</span>
- [`$F001F0` pixel mode 與 F003 的資料流](docs/f003-video-mode.md)
  <span class="note">bit 3 是 ROZ 的 tilemap／bitmap 切換，由自製卡帶定案。</span>

</div>

## 音訊

<div class="docs" markdown="1">

- [遊戲音效驅動與通訊協定](docs/sound-driver.md)
  <span class="note">68k↔65C02 mailbox、UM6619 暫存器語意、每通道 ADSR 包絡與取樣串流。</span>

</div>

## DMA

<div class="docs" markdown="1">

- [主機 DMA control 位元](docs/host-dma.md)
  <span class="note">觸發條件、byte／word 步進、`$A800` 特例，以及時序目前能說到哪裡。</span>

</div>

## 模擬器逆向與驗證

<div class="docs" markdown="1">

- [Bcan 模擬器逆向分析](docs/emulator-analysis.md)
  <span class="note">時脈、匯流排、存檔格式、音訊輸出管線，以及它比 MAME 多做的部分。</span>
- [逐遊戲驗證矩陣](docs/verify-matrix.md)
  <span class="note">九個本地映像的可重播檢查點與實際啟用的硬體圖層。</span>
- [測試結果截圖說明](docs/test-screenshots.md)
  <span class="note">每張截圖在證明什麼，以及判讀時踩過的五個坑。</span>
- [軟體模擬資料充分度評估](docs/emulation-readiness-assessment.md)
- [反編譯追資料流的方法與陷阱](docs/re-method-decompiler-dataflow.md)
- [文件完整度複查與可補來源](docs/documentation-review.md)

</div>

## 自製卡帶

商業 ROM 不會產生的硬體狀態，用自己寫的卡帶去製造，再與模擬器逐像素對拍。
產物含卡帶授權區，只留本機不進版控；原始碼與建置腳本都在 repo 裡。

<div class="docs" markdown="1">

- [bit3probe](homebrew/bit3probe/README.md)
  <span class="note">`$F001F0` bit 3 是 ROZ 的 tilemap／bitmap 切換。</span>
- [spriteprobe](homebrew/spriteprobe/README.md)
  <span class="note">四頁 87 個案例，掃 sprite 表的縮放、翻轉、mosaic 與 mask 模式。</span>
- [mosaicprobe](homebrew/mosaicprobe/README.md)
  <span class="note">一般圖層與 ROZ 的 mosaic 塊大小。</span>
- [dmaprobe](homebrew/dmaprobe/README.md)
  <span class="note">12 個 control 值的搬移結果與暫存器回讀。</span>
- [rich2demo](homebrew/rich2demo/README.md)
  <span class="note">把《大富翁2》台灣棋盤做成可跑的卡帶，驗證整條繪圖與輸入路徑。</span>

</div>

## 其他

<div class="docs" markdown="1">

- [工作歷程](WORKLOG.md)
  <span class="note">逐輪的量測、推翻與方法教訓。</span>
- [硬體圖片來源與授權](assets/hardware/README.md)
- [測試截圖的來源與邊界](assets/screenshots/README.md)

</div>
