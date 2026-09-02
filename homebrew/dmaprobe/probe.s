| Super A'Can homebrew：主機 DMA（$E90020／$E90030）control 位元的量測卡帶
|
| 每個案例先把目的區填成索引 255，再觸發一次 DMA，最後把六個 DMA 暫存器讀回寫進
| 另一塊 VRAM。畫面用 tilemap 把這兩塊都顯示出來：8bpp 之下一個 byte 就是一個像素，
| 調色盤把索引原樣編進顏色，所以截圖可以逐 byte 反推「搬了幾個、往哪個方向、
| 暫存器停在哪裡」。
|
| 視訊在跑 DMA 之前就設定好，萬一某個 control 值讓模擬器安全停機，畫面上仍看得到
| 停機前已完成的案例。

        .equ    VRAM,       0x00F40000
        .equ    VIDEO,      0x00F00000
        .equ    PALETTE,    0x00F00200
        .equ    DMA0,       0x00E90020

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

        | tile 0 清成 0（透明），tile 1 起全部填索引 255 當「未被搬到」的底色
        lea     VRAM,%a1
        move.w  #31,%d0
zero_loop:
        clr.w   (%a1)+
        dbra    %d0,zero_loop
        move.w  #2015,%d0               | tile 1..63：63×64 byte = 2016 word
fill_loop:
        move.w  #0xFFFF,(%a1)+
        dbra    %d0,fill_loop

        | tilemap -> VRAM byte $2000
        lea     map,%a0
        lea     VRAM+0x2000,%a1
        move.w  #1023,%d0
map_loop:
        move.w  (%a0)+,(%a1)+
        dbra    %d0,map_loop

        | 一般圖層 0：32×32、wrap、無 mosaic
        lea     VIDEO+0x100,%a1
        move.w  #0x0420,(%a1)
        move.w  #0x0000,2(%a1)
        move.w  #0x0000,4(%a1)
        move.w  #0x0000,6(%a1)
        move.w  #0x0800,8(%a1)          | map base：word index $1000
        move.w  #0x0000,10(%a1)
        move.w  #0x0000,12(%a1)
        move.w  #0x0000,14(%a1)

        lea     VIDEO,%a1
        move.w  #0x0180,8(%a1)          | 320 寬 ＋ 圖層 0
        move.w  #0x0002,0x1F0(%a1)      | gfx mode 2：圖層 0 走 8bpp

        | 等幾幀，確保畫面已經是「全部未搬」的狀態
        move.w  #7,%d6
warm_loop:
        bsr     wait_frame
        dbra    %d6,warm_loop

        | 逐案例觸發 DMA，並把六個暫存器讀回 VRAM byte $D40 起（tile 53，讓 13 個案例的資料區都排得下）
        lea     cases,%a0
        lea     VRAM+0xD40,%a2
        move.w  count,%d7
run_loop:
        lea     DMA0,%a1
        move.w  (%a0)+,(%a1)            | source 高位
        move.w  (%a0)+,2(%a1)           | source 低位
        move.w  (%a0)+,4(%a1)           | dest 高位
        move.w  (%a0)+,6(%a1)           | dest 低位
        move.w  (%a0)+,8(%a1)           | count
        move.w  (%a0)+,10(%a1)          | control（寫入即觸發）
        move.w  (%a1),(%a2)
        move.w  2(%a1),2(%a2)
        move.w  4(%a1),4(%a2)
        move.w  6(%a1),6(%a2)
        move.w  8(%a1),8(%a2)
        move.w  10(%a1),10(%a2)
        lea     64(%a2),%a2
        dbra    %d7,run_loop

idle:
        bsr     wait_frame
        bra     idle

| 等一次 vblank。$F00000 bit 15 是狀態旗標，讀取即清除。
wait_frame:
        movem.l %d0/%a4,-(%sp)
        lea     VIDEO,%a4
wf_wait:
        move.w  (%a4),%d0
        btst    #15,%d0
        beq     wf_wait
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
map:
        .incbin "build/map.bin"
        .org    0x2E00
cases:
        .incbin "build/cases.bin"
        .org    0x2F00
count:
        .include "build/count.inc"
        .org    0x3000
pattern:
        .incbin "build/pattern.bin"
