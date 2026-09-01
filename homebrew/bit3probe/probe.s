| Super A'Can homebrew: $F001F0 pixel-mode bit 3 probe
|
| ROZ 層以 8bpp region 運作（$F00180 的 mode & 3 == 3），並每 180 幀在
| $F001F0 的 $0001 與 $0009 之間切換，讓「pixel mode == $08 且 ROZ 8bpp」
| 這個在商業 ROM 上不可達的條件成立，供模擬器與實機對照。
|
| 調色盤第 255 號在切換時改色（bit 3 開為紅、關為藍），畫面左上角有一塊
| 索引 255 的方格，因此任何一張截圖都能自證當下處於哪個模式。

        .text
        .org    0

        .long   0x00FCFFFE              | vector 0: initial SSP
        .long   entry                   | vector 1: initial PC
        .rept   254
        .long   exception               | 其餘 exception 一律返回
        .endr

        .org    0x400
entry:
        move.w  #0x2700,%sr             | 遮蔽所有中斷，全程輪詢

        | 調色盤 256 word -> $F00200
        lea     palette,%a0
        lea     0x00F00200,%a1
        move.w  #255,%d0
pal_loop:
        move.w  (%a0)+,(%a1)+
        dbra    %d0,pal_loop

        | tile 圖樣 -> VRAM byte 0（8bpp，每 tile 64 byte）
        lea     tiles,%a0
        lea     0x00F40000,%a1
        move.w  #127,%d0                | 4 tiles = 256 byte = 128 word
tile_loop:
        move.w  (%a0)+,(%a1)+
        dbra    %d0,tile_loop

        | ROZ tilemap -> VRAM byte $2000（word index $1000）
        lea     rozmap,%a0
        lea     0x00F42000,%a1
        move.w  #1023,%d0               | 32*32 entries
map_loop:
        move.w  (%a0)+,(%a1)+
        dbra    %d0,map_loop

        | ROZ 暫存器
        lea     0x00F00180,%a1
        lea     rozmode,%a2             | ROZ mode 與 tile mode 由建置參數決定
        move.w  (%a2)+,0(%a1)
        move.w  (%a2),2(%a1)
        move.w  #0x0000,4(%a1)          | scroll X 高位
        move.w  #0x0000,6(%a1)          | scroll X 低位
        move.w  #0x0000,8(%a1)          | scroll Y 高位
        move.w  #0x0000,10(%a1)         | scroll Y 低位
        move.w  #0x0100,12(%a1)         | 係數 A：每像素 X 步進 1.0
        move.w  #0x0000,14(%a1)         | 係數 B
        move.w  #0x0000,16(%a1)         | 係數 C
        move.w  #0x0100,18(%a1)         | 係數 D：每行 Y 步進 1.0
        move.w  #0x0800,20(%a1)         | map base：word index $1000
        move.w  #0x0000,22(%a1)         | tile bank

        | video flags：320 寬 + ROZ 致能
        lea     0x00F00008,%a1
        move.w  #0x0104,(%a1)

        | 初始 pixel/gfx mode = $0001（bit 3 關）
        lea     0x00F001F0,%a3
        move.w  #0x0001,%d3
        move.w  %d3,(%a3)
        bsr     set_marker

        moveq   #0,%d2                  | 幀計數
main_loop:
        bsr     wait_frame
        addq.w  #1,%d2
        cmpi.w  #180,%d2
        blt     main_loop
        moveq   #0,%d2
        eori.w  #0x0008,%d3             | 切換 bit 3
        move.w  %d3,(%a3)
        bsr     set_marker
        bra     main_loop

| 依目前模式設定調色盤第 255 號：bit 3 開 = 紅，關 = 藍
set_marker:
        lea     0x00F003FE,%a2
        btst    #3,%d3
        beq     marker_off
        move.w  #0x001F,(%a2)
        rts
marker_off:
        move.w  #0x7C00,(%a2)
        rts

| 等一個完整的 vblank 邊緣：先等離開 vblank，再等進入 vblank
wait_frame:
        lea     0x00F00000,%a4
wait_active:
        move.w  (%a4),%d0
        btst    #15,%d0
        bne     wait_active
wait_blank:
        move.w  (%a4),%d0
        btst    #15,%d0
        beq     wait_blank
        rts

exception:
        rte

        .org    0x2000
auth:
        .incbin "build/auth.bin"        | 卡帶授權區，建置時由本機 ROM 取出

        .org    0x2400
palette:
        .incbin "build/palette.bin"

        .org    0x2600
tiles:
        .incbin "build/tiles.bin"

        .org    0x2800
rozmap:
        .incbin "build/rozmap.bin"

        .org    0x3800
rozmode:
        .include "build/rozmode.inc"
