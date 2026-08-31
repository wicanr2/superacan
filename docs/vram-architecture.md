# VRAM 實體架構與 128 KiB 視窗

更新日期：2026-08-31。本文專門區分 CPU 可見視窗、主機板實體容量，以及 UM6618 內部
位址產生器；三者不可混為同一件事。

## 1. 已證實的配線

`PCGAM 16000-2A` 的 U5、U6 是兩顆 `UM611024`（128K×8），一顆承載低 byte、另一顆承載
高 byte，組成 **128K×16 words＝256 KiB**。逆向繪製的 Eagle `PPU.sch` 明列下列 nets：

| UM6618 U12 | U5／U6 SRAM | 意義 |
|---|---|---|
| `VRAM_A1` | `A0` | 最低 word address bit |
| `VRAM_A2..A16` | `A1..A15` | 中間地址位 |
| `VRAM_A17` | `A16` | 最高 word address bit；選擇上下 64K-word 半區 |

因此 `VRAM_A17=0/1` 分別涵蓋 128 KiB，下半與上半合計 256 KiB。最高位不是懸空、綁低或
只接在未使用的大容量替代料上，而是由 UM6618 主動輸出。這是板級證據（p），來源為
[splash5/superacan-notes 的 `PPU.sch`](https://github.com/splash5/superacan-notes/blob/63731a2202ffa1ad829c49da8804a05b07a5943b/schematics/PPU.sch)。該圖是社群依主機板整理的
schematic，並非已取得的 UMC 原廠資料表，故仍應保留 provenance 邊界。

## 2. 為何 68000 仍只看到 128 KiB

68k bus map 的 `$F40000–$F5FFFF` 共 128 KiB，也就是 64K 個 16-bit word。MC68HC000 提供
一般 24-bit address bus、16-bit data bus 與 byte strobes；它不規定視訊記憶體如何分 bank。
CPU 對這個 window 提供的 word offset 只有 16 bits，而 UM6618 對 SRAM 可輸出 17 bits。

```text
MC68HC000：$F40000–$F5FFFF
       64K-word logical window
                 │
                 ▼
          UM6618 bus arbiter／address generator
                 │ VRAM_A1..A17
                 ▼
      2 × 128K×8 SRAM＝128K×16＝256 KiB
```

所以「同為 Motorola 68000 系列」只能幫助我們採用既有 CPU core；不能由 Mega Drive、
Neo Geo 或其他 68000 主機的 banking 規則推導 UM6618。banking／render address 是客製 ASIC
與板級 glue logic 的行為。

## 3. 尚未證實的行為

目前沒有證據指出某個 CPU-visible register 是「VRAM bank select」。BIOS 也無法補齊：IPL
完全不初始化 UM6618 或 VRAM，關閉 overlay 後便跳至卡帶程式。仍需確認的是：

1. tilemap、sprite、ROZ 或第四背景層的 base／tile bank 位是否在內部形成 `VRAM_A17`；
2. 主 DMA 或 sprite DMA 是否可把目的位址送到上半部；
3. `$F001F0` pixel／GFX mode 是否改變位址解讀；
4. 68k 的 128 KiB window 是否存在尚未觀察到的 bank switch。現有 Bcan／MAME bus map 都只
   支持固定 window，因此這是證據最弱的候選，不應先行實作。

## 4. 模擬器的保守實作契約

對 `16000-2A` hardware profile，建議配置 `0x20000` 個 16-bit words（256 KiB）實體 VRAM，
但維持 CPU window 為 `0x10000` words。renderer 與 DMA 使用獨立的 17-bit physical-address
helper，並記錄任何 bit 16 為 1 的存取；在找到 consumer 前，CPU 存取只落到已證實的下半區。

這種模型保留了板級能力，又不會把未知行為猜成一個虛構 bank register。驗證順序應為：

1. 靜態掃描十二款 ROM 對 UM6618 base、tile-bank、DMA 與 `$F001F0` 的寫入；
2. 在已可執行的模擬器中 trace renderer／DMA 的計算位址，觀察是否自然產生第 17 位；
3. 若軟體證據仍不足，在實機填入可辨識 pattern，量測 U12 `VRAM_A17`／SRAM `A16`；
4. 找到讀寫端後，再把欄位以「原始位址＋語意＋推論等級＋證據」回填 register 文件。

目前可下的最強結論是：**16000-2A 的 256 KiB 全部在 UM6618 的實體 address bus 上；CPU
如何或是否切換上半部、以及哪個繪圖功能使用它，仍未知。**
