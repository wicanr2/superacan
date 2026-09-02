| Super A'Can homebrew：UM6619 暫存器回讀掃描
|
| 65C02 對每個暫存器寫一次 $5A 再讀回，把回讀值存進 sound RAM $0700+n。
| 68k 等它掃完，再把 256 個值當成 tile 編號填進 ROZ 的 16×16 版面。
| tile n 整塊填索引 n，調色盤又把索引編回它自己，所以截圖能直接反推每一格的值。

        .equ    VRAM,       0x00F40000
        .equ    VIDEO,      0x00F00000
        .equ    PALETTE,    0x00F00200
        .equ    PROGRESS,   0x00E80600

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

        | 調色盤（索引 n 的顏色編回 n）
        lea     palette,%a0
        lea     PALETTE,%a1
        move.w  #255,%d0
pal_loop:
        move.w  (%a0)+,(%a1)+
        dbra    %d0,pal_loop

        | tile n 整塊填索引 n：256 張 × 64 byte
        lea     VRAM,%a1
        moveq   #0,%d1
tile_outer:
        move.w  %d1,%d0
        lsl.w   #8,%d0
        or.w    %d1,%d0                 | 一個 word 兩個 n
        moveq   #31,%d2
tile_inner:
        move.w  %d0,(%a1)+
        dbra    %d2,tile_inner
        addq.w  #1,%d1
        cmpi.w  #256,%d1
        blt     tile_outer

        | ROZ 版面先全部指到 tile 0
        lea     VRAM+0x8000,%a1
        move.w  #1023,%d0
        moveq   #0,%d1
map_clear:
        move.w  %d1,(%a1)+
        dbra    %d0,map_clear

        | ROZ：32×32、wrap、8bpp、1:1
        lea     VIDEO+0x180,%a1
        move.w  #0x0423,(%a1)
        move.w  #0x0000,2(%a1)
        move.w  #0x0000,4(%a1)
        move.w  #0x0000,6(%a1)
        move.w  #0x0000,8(%a1)
        move.w  #0x0000,10(%a1)
        move.w  #0x0100,12(%a1)         | 1:1；16×16 格 ×8px = 128×128，畫面放得下
        move.w  #0x0000,14(%a1)
        move.w  #0x0000,16(%a1)
        move.w  #0x0100,18(%a1)
        move.w  #0x2000,20(%a1)         | map base：VRAM byte $8000
        move.w  #0x0000,22(%a1)

        lea     VIDEO,%a1
        move.w  #0x0104,8(%a1)          | 320 寬 ＋ ROZ
        move.w  #0x0002,0x1F0(%a1)

        | 上傳 65C02 驅動到 sound RAM $0500，設 reset 向量，放開重置
        lea     sounddrv,%a0
        movea.l #0x00E80500,%a1
        move.w  drvlen,%d0
snd_loop:
        move.b  (%a0)+,(%a1)+
        dbra    %d0,snd_loop
        movea.l #0x00E8FFFC,%a1
        move.b  #0x00,(%a1)+
        move.b  #0x05,(%a1)
        movea.l #0x00E9001C,%a1
        move.w  release,(%a1)           | 建置參數：1 放開 65C02、0 保持重置

        | 底色改成亮綠：這樣「沒在跑」（全黑）與「在跑但還沒掃到」分得開
        move.w  #0x03E0,(0x00F00200).l

main_loop:
        bsr     wait_frame

        | 每幀都把 $0700–$07FF 畫成 16×16 色格（ROZ 版面每列 32 word）。
        | 不等完成旗標，停在半路也看得出停在哪。
        movea.l #0x00E80700,%a0
        lea     VRAM+0x8000,%a1
        moveq   #0,%d2                  | 列
grid_row:
        moveq   #0,%d3                  | 欄
grid_col:
        moveq   #0,%d0
        move.b  (%a0)+,%d0
        move.w  %d2,%d1
        lsl.w   #5,%d1                  | 列 × 32 word
        add.w   %d3,%d1
        add.w   %d1,%d1                 | word → byte
        move.w  %d0,0(%a1,%d1.w)
        addq.w  #1,%d3
        cmpi.w  #16,%d3
        blt     grid_col
        addq.w  #1,%d2
        cmpi.w  #16,%d2
        blt     grid_row

        bra     main_loop

wait_frame:
        movem.l %d0/%a4,-(%sp)
        lea     VIDEO,%a4
wf_active:
        move.w  (%a4),%d0
        btst    #15,%d0
        bne     wf_active
wf_blank:
        move.w  (%a4),%d0
        btst    #15,%d0
        beq     wf_blank
        movem.l (%sp)+,%d0/%a4
        rts

exception:
        rte

        .org    0x2000
auth:
        .incbin "build/auth.bin"
        .org    0x2400
palette:
        .incbin "build/palette.bin"
        .org    0x2600
sounddrv:
        .incbin "build/sounddrv.bin"
        .org    0x2700
drvlen:
        .include "build/drvlen.inc"
        .org    0x2800
release:
        .include "build/release.inc"
