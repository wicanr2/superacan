| Super A'Can homebrew：tilemap／ROZ 的 mosaic 量測卡帶
|
| 畫面鋪滿 16×16 的解碼圖樣：像素值 ＝ (x&7) + 8×(y&7) + 64×t，t 由 tile 在 2×2
| 區塊中的位置決定。調色盤把這三個分量分別編進紅、綠、藍，因此截圖上每個像素都能
| 反推它取樣自來源的哪一格，mosaic 的塊大小與塊原點可以直接量出來，不必從外框猜。
|
| 建置參數決定要看的是一般圖層 0 還是 ROZ，以及 mosaic 欄位的值；兩組暫存器都會寫，
| 只有 video flags 決定哪一層被畫出來。

        .equ    VRAM,       0x00F40000
        .equ    VIDEO,      0x00F00000
        .equ    PALETTE,    0x00F00200

        .text
        .org    0

        .long   0x00FCFFFE              | vector 0: initial SSP
        .long   entry                   | vector 1: initial PC
        .rept   254
        .long   exception
        .endr

        .org    0x400
entry:
        move.w  #0x2700,%sr             | 遮蔽所有中斷，全程輪詢

        lea     cfg,%a2
        move.w  (%a2)+,%d1              | video flags
        move.w  (%a2)+,%d2              | pixel／gfx mode
        move.w  (%a2)+,%d3              | 一般圖層 0 的 flags
        move.w  (%a2)+,%d4              | ROZ 的 mode

        | 調色盤 256 word -> $F00200
        lea     palette,%a0
        lea     PALETTE,%a1
        move.w  #255,%d0
pal_loop:
        move.w  (%a0)+,(%a1)+
        dbra    %d0,pal_loop

        | 清 VRAM 前 16 KiB，避免殘留圖形混進判讀
        lea     VRAM,%a1
        move.w  #4095,%d0
clr_loop:
        clr.l   (%a1)+
        dbra    %d0,clr_loop

        | 四張解碼 tile -> VRAM byte 0（8bpp，每張 64 byte）
        lea     tile,%a0
        lea     VRAM,%a1
        move.w  #127,%d0
tile_loop:
        move.w  (%a0)+,(%a1)+
        dbra    %d0,tile_loop

        | 32×32 tilemap -> VRAM byte $2000（word index $1000）
        lea     map,%a0
        lea     VRAM+0x2000,%a1
        move.w  #1023,%d0
map_loop:
        move.w  (%a0)+,(%a1)+
        dbra    %d0,map_loop

        | 一般圖層 0
        lea     VIDEO+0x100,%a1
        move.w  %d3,(%a1)               | 尺寸 32×32、wrap、mosaic
        move.w  #0x0000,2(%a1)          | 無逐行捲動
        move.w  #0x0000,4(%a1)          | scroll X
        move.w  #0x0000,6(%a1)          | scroll Y
        move.w  #0x0800,8(%a1)          | map base：word index $1000
        move.w  #0x0000,10(%a1)         | tile bank
        move.w  #0x0000,12(%a1)
        move.w  #0x0000,14(%a1)

        | ROZ：identity 變換，指向同一份 tilemap
        lea     VIDEO+0x180,%a1
        move.w  %d4,(%a1)               | region 3（8bpp）、wrap、mosaic
        move.w  #0x0000,2(%a1)
        move.w  #0x0000,4(%a1)          | scroll X 高位
        move.w  #0x0000,6(%a1)          | scroll X 低位
        move.w  #0x0000,8(%a1)          | scroll Y 高位
        move.w  #0x0000,10(%a1)         | scroll Y 低位
        move.w  #0x0100,12(%a1)         | A：每像素 X 步進 1.0
        move.w  #0x0000,14(%a1)         | B
        move.w  #0x0000,16(%a1)         | C
        move.w  #0x0100,18(%a1)         | D：每行 Y 步進 1.0
        move.w  #0x0800,20(%a1)         | map base：word index $1000
        move.w  #0x0000,22(%a1)         | tile bank

        lea     VIDEO,%a1
        move.w  %d1,8(%a1)              | video flags
        move.w  %d2,0x1F0(%a1)          | pixel／gfx mode

idle:
        bra     idle

exception:
        rte

        .org    0x2000
auth:
        .incbin "build/auth.bin"
        .org    0x2400
palette:
        .incbin "build/palette.bin"
        .org    0x2600
tile:
        .incbin "build/tile.bin"
        .org    0x2700
map:
        .incbin "build/map.bin"
        .org    0x2F00
cfg:
        .include "build/cfg.inc"
