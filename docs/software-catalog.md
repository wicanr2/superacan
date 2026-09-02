# Super A'Can 正式軟體目錄與本地 ROM 對照

來源為固定 MAME commit `6ae579aed3107c0b42c1c1c5cb05c02df4456eff` 的
[`hash/supracan.xml`](https://github.com/mamedev/mame/blob/6ae579aed3107c0b42c1c1c5cb05c02df4456eff/hash/supracan.xml)
（CC0-1.0）。該 snapshot 明記「All known released games are dumped」，並列出 F001–F012。
這是 MAME 軟體保存目錄，不代表每款在 MAME 或本專案模擬器中均可完整遊玩。

## 1. 十二款正式遊戲

| Serial | MAME ID | 年 | 發行商 | 英文／羅馬字標題 | 中文標題 | ROM |
|---|---|---:|---|---|---|---:|
| F001 | `formduel` | 1995 | AV Artisan | Formosa Duel / Formosa Da Dui Jue | 福爾摩沙大對決 | 1 MiB |
| F002 | `sangofgt` | 1995 | Panda Entertainment Technology | Sango Fighter / Wu Jiang Zheng Ba - San Guo Zhi | 三國志 武將爭霸 | 3 MiB |
| F003 | `sonevil` | 1995 | Funtech | The Son of Evil / Xie E Zhi Zi | 邪惡之子 | 2 MiB |
| F004 | `speedyd` | 1995 | AV Artisan | Speedy Dragon / Yin Su Fei Long | 音速飛龍 | 2 MiB |
| F005 | `staiwbbl` | 1995 | C&E | Super Taiwanese Baseball League / Chao Ji Zhong Hua Zhi Bang Lian Meng | 超級中華職棒聯盟 | 2 MiB |
| F006 | `jttlaugh` | 1995 | Funtech | Journey to the Laugh / Xi You Ji | 嘻遊記 | 2 MiB |
| F007 | `slghtsag` | 1996 | Kingformation（＝**精訊資訊有限公司**，見下）| Super Light Saga - Dragon Force / Chao Ji Guang Ming Zhan Shi | 超級光明戰史 | 2 MiB＋1 MiB |
| F008 | `monopoly` | 1995 | Panda Entertainment Technology | Monopoly: Adventure in Africa / Fei Zhou Tan Xian Da Fu Weng | 非洲探險 | 1 MiB |
| F009 | `gamblord` | 1996 | Funtech | Gambling Lord / Du Ba | 賭霸 | 2 MiB |
| F010 | `magipool` | 1996 | Funtech | Magical Pool / Mo Bang Zhuang Qiu | 魔棒撞球 | 2 MiB |
| F011 | `boomzoo` | 1996 | Funtech | Boom Zoo / Bao Bao Dong Wu Yuan | 爆爆動物園 | 512 KiB |
| F012 | `rebelst` | 1996 | Horng Shen Information | Rebel Star / Pàn Xīng | 叛星 | 2 MiB |

MAME snapshot 另列四個未發售卡帶名稱：Dinosaur Wars、City Escape、Quick Fighting Attack、
Journey to the Center of the Earth。這只表示該目錄明列四項，不足以否定其他曾規劃但未記錄的
專案；因此不再沿用來源不明的「約 11 款未發售」作確定數量。

## 2. 本地研究映像

本地 `Bcan008b/ROMS/` 有九款內容，CRC32／SHA-1 全部精確匹配 MAME catalog；缺 F009、F010、
F012。檔名是本機歷史名稱，不等於正式產品標題。

| 本地檔案 | 對應 | CRC32 | SHA-1 | SHA-256 |
|---|---|---|---|---|
| `Formosa Duel (Taiwan).bin` | F001 | `b2bf31dc` | `8d0680e1322af21b20d5cee2c100b05cf4217815` | `d6697e349613f70812cb7815de04bd89027d7e5b72471a981d16f6c667099b99` |
| `Sango Fighter (Taiwan).bin` | F002 | `a4de6dde` | `f4bed63775130a75eb9c50b32e0cf50d1a7b8f50` | `bb4f38089f8350a9f4005956b223300f8763f2ff9ca04d471329704d8e78e9f3` |
| `The Son of Evil (Taiwan).bin` | F003 | `9f6119a7` | `67ae9e7f99e1c3054ea54d53dbbba7792ef45134` | `791ab9d5ca182830fcf8ded488e71f1b61398da84967543396d0496e11bf5deb` |
| `Speedy Dragon (Taiwan).bin` | F004 | `f631383c` | `fbd62b5d287aa82ef27f400ab2a6b3da0308192a` | `dfba00a46e7d71b9d78688bd902ec05e2c353f2ff119273d47b0a02602f3c9a2` |
| `Super Taiwanese Baseball League (Taiwan).bin` | F005 | `ccf6829b` | `17a413803d8749fbe9643ca56d703afd64569b9f` | `e0c17fcd21341c2416b19a830117db5898e6fd6995f41559bf7dd5ace745bd4e` |
| `Journey to the Laugh (Taiwan).bin` | F006 | `cee25eea` | `fc82fc3a7d55571494cd62d8807160e22cf437bc` | `a4964b702214f70e199bb07bbd2777eb08875206fa27396989f2a79cb48c5087` |
| `Super Dragon Force (Taiwan).zip` | F007（內容；本地容器誤命名） | 見 §3 | 見 §3 | 見 §3 |
| `Monopoly - Adventure in Africa (Taiwan).bin` | F008 | `dc3b7b84` | `6dcbd7923203da7892915595d65ee668afbf0339` | `b90b8dbfd15f1bcdd3e8f70910fa2f69effe07f2c781d04b123b738813fecb2f` |
| `Boom Zoo (Taiwan).bin` | F011 | `6099bb44` | `0b5fbe2117bb77a827453c5489b3af691e5c7ade` | `090827d00ef8047d2c78cc173d258565b1c3ab01f0d97dc3ed8e08833d370077` |

ROM／BIOS 是本機研究輸入，不加入 Git 或公開發行包；hash 台帳可公開用於辨識，不包含遊戲內容。

### 2.1 F007 的開發商即精訊資訊有限公司

1995 年 10 月的《A'can 特輯》有一篇「精訊特別報導」，訪問**精訊資訊有限公司**，
該公司正在開發《超級光明戰史》對應「A'CAN F-16」主機，訪談配圖的門牌英文社名以
「…formation Co., Ltd.」形式出現。MAME catalog 記的 `Kingformation` 即此公司。

同一篇訪談也交代了年份：受訪者稱「原本的超級光明戰史是要同主機發售」，後有時間上的
調度，延誤的最大因素是人員流失（美工多為十八至二十歲、面臨兵役）。主機 1995 年 10 月
發售、本作 1996 年才出，時間差在當月的訪談裡已有說明。詳見
[console-history.md](console-history.md) §2.3 與 [history/精訊資訊有限公司.md](history/精訊資訊有限公司.md)。

## 3. F007 雙部分卡帶訂正

本地 ZIP 名稱與其中 `08002 (Taiwan).bin` 的檔名都不可靠，但內容 hash 已定案：

| 本地成員 | 大小 | CRC32 | SHA-1 | MAME 正式成員 |
|---|---:|---|---|---|
| `16007 (Taiwan).bin` | 2 MiB | `56c1c3fb` | `249e2ad6d8d40ecd31eda5a1bd5e5d0f47174a27` | `16007.0` |
| `08002 (Taiwan).bin` | 1 MiB | `fc79f05f` | `7ce2e23ea3fd25764935708be4d47bf1a9843938` | `08007.1` |

兩個 hash 均精確匹配 F007 `slghtsag`，故本地內容是 **Super Light Saga - Dragon Force／
超級光明戰史**，不是另一款「Super Dragon Force／超級龍虎霸」。分析工具應依 hash 與 part
offset 組合，不應依這個歷史 ZIP／成員檔名路由。

## 4. NVRAM 資訊邊界

MAME catalog 對 F003、F005、F007、F008、F009、F012 宣告 32 KiB `nvram` dataarea，但每項均
附「size 未確認」，F009 連實體存在與否也未確認。這可作模擬器建立 32 KiB SRAM fallback 的
軟體清單提示，不能當作所有實體卡帶 PCB 都裝有 SRAM／電池的板級證據。

## 5. MAME 相容性 metadata 的解讀

固定 catalog 的 `supported` 是 MAME 當時的軟體狀態，不是遊戲 dump 品質：F001、F004、F005、
F012 為 `no`，其餘為 `partial`。逐遊戲 notes 指向的共同硬體缺口集中於：

- UM6618 per-tile priority、ROZ paging／blending、window clipping 與 sprite buffering；
- IRQ3 FRC 的遊戲速度；
- UM6619 高通道 release／重複播放及 DMA sample completion。

這些 notes 適合作相容性測試情境，不能直接當作真實硬體 register 定義。
