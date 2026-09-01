| Super A'Can homebrew：大富翁2 台灣棋盤 demo
|
| 以原版的 11×11 地圖視窗顯示台灣棋盤，按 A 擲骰、棋子沿道路網移動，
| 岔路由方向鍵決定走哪一條。
|
| 畫面組法：11×11 個 24×20 的原版地圖圖磚攤成 264×220 的畫布，寫進 VRAM 時
| 直接排成 8×8 packed 8bpp tile（33×28＝924 張），tilemap 以線性索引指過去。
| 24 是 8 的倍數，所以每一列來源正好落在三張相鄰 tile 的同一列，搬移只是
| 「三段 8 bytes、間隔 64」。

        .equ    VRAM,       0x00F40000
        .equ    VIDEO,      0x00F00000
        .equ    PALETTE,    0x00F00200
        .equ    PADPORT,    0x00E80200

        .equ    TILEBASE,   VRAM+0x00000    | 924 張 8×8 tile
        .equ    MAPBASE,    VRAM+0x12000    | 64×32 tilemap

        .equ    WRAM,       0x00FC0000
        .equ    cur,        WRAM+0
        .equ    prev,       WRAM+2
        .equ    originRow,  WRAM+4
        .equ    originCol,  WRAM+6
        .equ    vrow,       WRAM+8
        .equ    vcol,       WRAM+10
        .equ    rng,        WRAM+12
        .equ    prevpad,    WRAM+14
        .equ    steps,      WRAM+16
        .equ    cand,       WRAM+18         | 最多四個候選格號
        .equ    waitcnt,    WRAM+32

        .text
        .org    0

        .long   0x00FCFFFE              | vector 0：初始 SSP
        .long   entry                   | vector 1：初始 PC
        .rept   254
        .long   exception
        .endr

        .org    0x400
entry:
        move.w  #0x2700,%sr             | 全程輪詢，不用中斷

        | ---- 調色盤 ----
        lea     palette,%a0
        lea     PALETTE,%a1
        move.w  #255,%d0
pal_loop:
        move.w  (%a0)+,(%a1)+
        dbra    %d0,pal_loop

        | ---- 清掉 tile 區（含空白 tile 1023）----
        lea     VRAM,%a1
        move.w  #0x3FFF,%d0             | 16384 個 long = 64 KiB
clr_loop:
        clr.l   (%a1)+
        dbra    %d0,clr_loop

        | ---- 線性 tilemap：可視的 33×28 指向 tile 0..923，其餘指空白 ----
        lea     MAPBASE,%a1
        moveq   #0,%d2
mt_row:
        moveq   #0,%d3
mt_col:
        move.w  #1023,%d0
        cmpi.w  #28,%d2
        bge     mt_put
        cmpi.w  #33,%d3
        bge     mt_put
        move.w  %d2,%d0
        mulu    #33,%d0
        add.w   %d3,%d0
mt_put:
        move.w  %d0,(%a1)+
        addq.w  #1,%d3
        cmpi.w  #64,%d3
        blt     mt_col
        addq.w  #1,%d2
        cmpi.w  #32,%d2
        blt     mt_row

        | ---- tilemap 0 暫存器 ----
        lea     VIDEO+0x100,%a1
        move.w  #0xE600,(%a1)           | 優先度 7、64×32、不 wrap
        move.w  #0x0000,2(%a1)          | tile mode
        move.w  #0x0FE4,4(%a1)          | scroll X = -28，把 264 寬置中
        move.w  #0x0FF6,6(%a1)          | scroll Y = -10
        move.w  #0x4800,8(%a1)          | map base
        move.w  #0x0000,10(%a1)         | mode（tile bank 0）

        | ---- 顯示模式 ----
        lea     VIDEO,%a1
        move.w  #0x0180,8(%a1)          | 320 寬 ＋ normal layer 0
        move.w  #0x0002,0x1F0(%a1)      | gfx mode 2：layer 0 為 8bpp

        | ---- 手把：把掃描迴圈上傳到 65C02 並放開重置 ----
        lea     sounddrv,%a0
        movea.l #0x00E80500,%a1
        moveq   #41-1,%d0
snd_loop:
        move.b  (%a0)+,(%a1)+
        dbra    %d0,snd_loop
        movea.l #0x00E8FFFC,%a1
        move.b  #0x00,(%a1)+            | reset 向量 = $0500
        move.b  #0x05,(%a1)
        movea.l #0x00E9001C,%a1
        move.w  #0x0001,(%a1)           | bit0 = 1：放開 65C02

        | ---- 初始狀態 ----
        move.w  start,%d0
        move.w  %d0,cur
        clr.w   prev
        clr.w   rng
        move.w  #0x00FF,prevpad
        bsr     recenter
        bsr     render
        bsr     draw_token

main_loop:
        bsr     wait_frame
        addq.w  #1,rng
        bsr     read_pad
        move.w  %d0,%d1
        move.w  prevpad,%d2
        not.w   %d2
        and.w   %d2,%d1                 | 這一幀新按下的
        move.w  %d0,prevpad
        btst    #7,%d1                  | A
        beq     main_loop
        bsr     roll_and_move
        bra     main_loop

| ---------------------------------------------------------------- 擲骰與移動
roll_and_move:
        moveq   #0,%d0
        move.w  rng,%d0
        divu    #6,%d0
        swap    %d0
        andi.l  #0xFFFF,%d0
        addq.w  #1,%d0
        move.w  %d0,steps
rm_step:
        bsr     next_square
        bsr     recenter
        bsr     render
        bsr     draw_token
        moveq   #10,%d0
rm_delay:
        bsr     wait_frame
        addq.w  #1,rng
        subq.w  #1,%d0
        bne     rm_delay
        subq.w  #1,steps
        bne     rm_step
        rts

| 決定下一格：排掉來時路，只剩一條就直接走，多條就等方向鍵。
next_square:
        bsr     square_addr             | %a0 = 目前格的資料
        lea     cand,%a1
        moveq   #0,%d3                  | 候選數
        moveq   #0,%d4
ns_loop:
        move.w  4(%a0,%d4.w),%d5
        tst.w   %d5
        beq     ns_next
        cmp.w   prev,%d5
        beq     ns_next
        move.w  %d5,(%a1)+
        addq.w  #1,%d3
ns_next:
        addq.w  #2,%d4
        cmpi.w  #8,%d4
        blt     ns_loop

        tst.w   %d3
        bne     ns_have
        move.w  prev,%d5                | 死路才准回頭
        bra     ns_take
ns_have:
        cmpi.w  #1,%d3
        bne     ns_wait
        move.w  cand,%d5
        bra     ns_take

ns_wait:
        clr.w   waitcnt
ns_choose:
        bsr     wait_frame
        addq.w  #1,rng
        addq.w  #1,waitcnt
        cmpi.w  #60,waitcnt
        bge     ns_auto
        bsr     read_pad
        move.w  %d0,%d6
        lea     cand,%a1
        move.w  %d3,%d7
        subq.w  #1,%d7
nc_loop:
        move.w  (%a1)+,%d5
        bsr     dir_of                  | %d0 = 0 上 1 下 2 左 3 右
        moveq   #3,%d1
        sub.w   %d0,%d1                 | 上 bit3、下 bit2、左 bit1、右 bit0
        btst    %d1,%d6
        bne     ns_take
        dbra    %d7,nc_loop
        bra     ns_choose

| 一秒內沒指定方向就照原版的做法隨機挑一條。
ns_auto:
        moveq   #0,%d0
        move.w  rng,%d0
        divu    %d3,%d0
        swap    %d0
        andi.l  #0xFFFF,%d0
        add.w   %d0,%d0
        lea     cand,%a1
        move.w  0(%a1,%d0.w),%d5

ns_take:
        move.w  cur,prev
        move.w  %d5,cur
        rts

| %d5 的格號相對目前格在哪個方向；只看主要分量。
dir_of:
        movem.l %d2-%d4/%a0,-(%sp)
        bsr     square_addr
        move.w  (%a0),%d2               | 目前格的螢幕 X 格座標
        move.w  2(%a0),%d3              | 螢幕 Y
        move.w  %d5,%d0
        bsr     square_addr_d0
        move.w  (%a0),%d4
        sub.w   %d2,%d4                 | dx
        move.w  2(%a0),%d0
        sub.w   %d3,%d0                 | dy
        move.w  %d4,%d2
        bpl     do_absx
        neg.w   %d2
do_absx:
        move.w  %d0,%d3
        bpl     do_absy
        neg.w   %d3
do_absy:
        cmp.w   %d3,%d2
        ble     do_vert
        tst.w   %d4
        bmi     do_left
        moveq   #3,%d0
        bra     do_done
do_left:
        moveq   #2,%d0
        bra     do_done
do_vert:
        tst.w   %d0
        bmi     do_up
        moveq   #1,%d0
        bra     do_done
do_up:
        moveq   #0,%d0
do_done:
        movem.l (%sp)+,%d2-%d4/%a0
        rts

| %a0 ← 目前格的資料位址
square_addr:
        move.w  cur,%d0
| %a0 ← %d0 指定格號的資料位址
square_addr_d0:
        ext.l   %d0
        subq.l  #1,%d0
        mulu    #12,%d0
        lea     squares,%a0
        adda.l  %d0,%a0
        rts

| ---------------------------------------------------------------- 視窗與繪圖
| 視窗中心跟著目前格，前後各留 5 格並夾在 0..25。
recenter:
        bsr     square_addr
        move.w  2(%a0),%d1
        bsr     clamp_origin
        move.w  %d1,originRow
        move.w  (%a0),%d1
        bsr     clamp_origin
        move.w  %d1,originCol
        rts

clamp_origin:
        subq.w  #5,%d1
        bge     co_high
        moveq   #0,%d1
co_high:
        cmpi.w  #25,%d1
        ble     co_done
        move.w  #25,%d1
co_done:
        rts

| 把 11×11 個地圖圖磚攤進 VRAM 的 tile 版面。
render:
        clr.w   vrow
rv_row:
        clr.w   vcol
rv_col:
        move.w  originRow,%d0
        add.w   vrow,%d0
        mulu    #36,%d0
        move.w  originCol,%d1
        add.w   vcol,%d1
        ext.l   %d1
        add.l   %d1,%d0
        lea     terrain,%a0
        moveq   #0,%d1
        move.b  0(%a0,%d0.l),%d1
        mulu    #480,%d1
        lea     maptiles,%a2
        adda.l  %d1,%a2                 | 來源圖磚

        move.w  vrow,%d0
        mulu    #20,%d0                 | 這一格的第一列 Y
        move.w  vcol,%d1
        mulu    #3,%d1                  | 起始 tile 欄
        lea     VRAM,%a1
        moveq   #19,%d7
        moveq   #0,%d2
rv_line:
        move.w  %d0,%d3
        add.w   %d2,%d3                 | Y
        moveq   #0,%d4
        move.w  %d3,%d4
        lsr.l   #3,%d4                  | tile 列
        mulu    #33,%d4
        add.l   %d1,%d4
        lsl.l   #6,%d4                  | ×64：tile 在 VRAM 的位移
        move.w  %d3,%d6
        andi.w  #7,%d6
        lsl.w   #3,%d6                  | tile 內的列
        ext.l   %d6
        add.l   %d6,%d4
        lea     0(%a1,%d4.l),%a3
        move.l  (%a2)+,(%a3)
        move.l  (%a2)+,4(%a3)
        move.l  (%a2)+,64(%a3)
        move.l  (%a2)+,68(%a3)
        move.l  (%a2)+,128(%a3)
        move.l  (%a2)+,132(%a3)
        addq.w  #1,%d2
        dbra    %d7,rv_line

        addq.w  #1,vcol
        cmpi.w  #11,vcol
        blt     rv_col
        addq.w  #1,vrow
        cmpi.w  #11,vrow
        blt     rv_row
        rts

| 把棋子蓋進剛畫好的 tile 版面。X 一定是 8 的倍數，所以每一列只落在一張 tile 上；
| 值 0 視為透明，直接跳過。
draw_token:
        bsr     square_addr
        move.w  (%a0),%d1
        sub.w   originCol,%d1
        mulu    #24,%d1
        addi.w  #8,%d1                  | 格內置中的 X
        move.w  2(%a0),%d2
        sub.w   originRow,%d2
        mulu    #20,%d2
        addi.w  #6,%d2                  | 格內置中的 Y
        lea     token,%a2
        lea     VRAM,%a1
        moveq   #7,%d7
dt_row:
        moveq   #0,%d4
        move.w  %d2,%d4
        lsr.l   #3,%d4
        mulu    #33,%d4                 | tile 列
        moveq   #0,%d5
        move.w  %d1,%d5
        lsr.w   #3,%d5
        add.l   %d5,%d4                 | ＋ tile 欄
        lsl.l   #6,%d4                  | ×64
        moveq   #0,%d6
        move.w  %d2,%d6
        andi.w  #7,%d6
        lsl.w   #3,%d6
        add.l   %d6,%d4
        lea     0(%a1,%d4.l),%a3
        moveq   #7,%d0
dt_px:
        move.b  (%a2)+,%d6
        beq     dt_skip
        move.b  %d6,(%a3)
dt_skip:
        addq.l  #1,%a3
        dbra    %d0,dt_px
        addq.w  #1,%d2
        dbra    %d7,dt_row
        rts

| ---------------------------------------------------------------- 輸入與同步
| 65C02 掃描的結果放在 sound RAM $0200：bit7 A、bit6 B、bit5 Start、bit4 Select、
| bit3 上、bit2 下、bit1 左、bit0 右，1 = 按下。
read_pad:
        movea.l #PADPORT,%a0
        moveq   #0,%d0
        move.b  (%a0),%d0
        rts

| 等一個完整的幀邊界：先等離開 vblank，再等進入 vblank。
| 呼叫端常把迴圈計數放在 %d0，所以這裡不留任何副作用。
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
        .incbin "build/auth.bin"        | 卡帶授權區，建置時由本機 ROM 取出
        .org    0x2400
palette:
        .incbin "build/palette.bin"
        .org    0x2600
squares:
        .incbin "build/squares.bin"
        .org    0x3000
terrain:
        .incbin "build/terrain.bin"
        .org    0x3600
token:
        .incbin "build/token.bin"
        .org    0x3680
sounddrv:
        .incbin "build/sounddrv.bin"
        .org    0x3700
start:
        .include "build/start.inc"
        .org    0x4000
maptiles:
        .incbin "build/maptiles.bin"
