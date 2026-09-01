| Super A'Can homebrew：sprite 表欄位的量測卡帶
|
| 畫面是純底色加一個 4×6 的 sprite 網格，每格只差一個欄位值。因為底色與 sprite
| 圖形都是單一顏色，量白色方框的外接矩形就直接得到該欄位造成的寬高。

        .equ    VRAM,       0x00F40000
        .equ    VIDEO,      0x00F00000
        .equ    PALETTE,    0x00F00200
        .equ    SPRTABLE,   VRAM+0x1000     | word index $0800

        .text
        .org    0

        .long   0x00FCFFFE
        .long   entry
        .rept   254
        .long   exception
        .endr

        .org    0x400
entry:
        move.w  #0x2700,%sr

        | 調色盤
        lea     palette,%a0
        lea     PALETTE,%a1
        move.w  #255,%d0
pal_loop:
        move.w  (%a0)+,(%a1)+
        dbra    %d0,pal_loop

        | 清 VRAM 前 8 KiB，確保沒有殘留圖形干擾判讀
        lea     VRAM,%a1
        move.w  #2047,%d0
clr_loop:
        clr.l   (%a1)+
        dbra    %d0,clr_loop

        | sprite 圖形：四張解碼 tile 放在 tile 1..4（VRAM byte 64 起）
        lea     tile,%a0
        lea     VRAM+64,%a1
        move.w  #127,%d0                | 4 tile × 64 byte = 128 word
tile_loop:
        move.w  (%a0)+,(%a1)+
        dbra    %d0,tile_loop

        | 子 tile 表：VRAM byte $1800（word index $C00）
        lea     subtable,%a0
        lea     VRAM+0x1800,%a1
        move.w  #11,%d0
sub_loop:
        move.w  (%a0)+,(%a1)+
        dbra    %d0,sub_loop

        | sprite 表
        lea     sprites,%a0
        lea     SPRTABLE,%a1
        move.w  count,%d0
        addq.w  #1,%d0
        lsl.w   #2,%d0                  | 每筆 4 word
        subq.w  #1,%d0
spr_loop:
        move.w  (%a0)+,(%a1)+
        dbra    %d0,spr_loop

        lea     VIDEO+0x20,%a1
        move.w  #0x0400,(%a1)           | sprite table base（word index $0800）
        move.w  count,2(%a1)            | 筆數 − 1
        move.w  #0x0000,4(%a1)
        move.w  #0x0001,6(%a1)          | 8bpp

        lea     VIDEO,%a1
        move.w  #0x0108,8(%a1)          | 320 寬 ＋ sprite，不開任何 tilemap
        move.w  #0x0002,0x1F0(%a1)

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
        .incbin "build/tile.bin"        | 四張解碼 tile，共 256 byte
        .org    0x2700
subtable:
        .incbin "build/subtable.bin"
        .org    0x2800
sprites:
        .incbin "build/sprites.bin"
        .org    0x2900
count:
        .include "build/count.inc"
