// 從《大富翁2》的原版檔案匯出 demo 卡帶需要的素材。
//
// 直接呼叫 rich2 專案 internal/assets 的解析器，不重寫格式解讀——那份已由該專案
// 逐 byte 對帳過。因為 Go 的 internal 套件不能跨模組 import，執行方式是把 rich2 的
// go.mod／go.sum／internal 複製成一份暫時模組，再把本檔放進 cmd/dump/：
//
//	mkdir -p /tmp/r2mod/cmd/dump
//	cp ~/cht/rich2/{go.mod,go.sum} /tmp/r2mod/
//	cp -r ~/cht/rich2/internal /tmp/r2mod/internal
//	cp export/main.go /tmp/r2mod/cmd/dump/main.go
//	cd /tmp/r2mod && go run ./cmd/dump <RICH2 目錄> <輸出目錄> SAVE_2.DSK
//
// 輸出四個檔案全部是原版衍生資料，不得進版控。
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/anr2/rich2/internal/assets"
)

func must(err error) {
	if err != nil {
		panic(err)
	}
}

// square 是棋盤的最小可用切片：地圖座標、四個方向的鄰接格號，加上判斷格種所需的欄位。
type square struct {
	N, Row, Col, Land, Order, Kind int
	Link                           [4]int
}

func main() {
	if len(os.Args) != 4 {
		fmt.Fprintln(os.Stderr, "用法：dump <RICH2 目錄> <輸出目錄> <存檔檔名>")
		os.Exit(2)
	}
	root, out, saveName := os.Args[1], os.Args[2], os.Args[3]

	save, err := os.ReadFile(filepath.Join(root, saveName))
	must(err)
	board, err := assets.ParseBoard(save)
	must(err)
	layers, err := assets.ParseMapLayers(save)
	must(err)
	part, err := os.ReadFile(filepath.Join(root, "PART1.PAK"))
	must(err)
	tiles, err := assets.DecodeMapTiles(part)
	must(err)
	palRaw, err := os.ReadFile(filepath.Join(root, "256.PAT"))
	must(err)
	pal, err := assets.ParsePalette(palRaw)
	must(err)

	minRow, minCol, maxRow, maxCol := 999, 999, -1, -1
	var squares []square
	for n := 1; n <= board.Count; n++ {
		s := board.Square[n]
		if !s.InUse {
			continue
		}
		squares = append(squares, square{n, s.Row, s.Col, s.Land, s.Order, s.Kind, s.Link})
		minRow, maxRow = min(minRow, s.Row), max(maxRow, s.Row)
		minCol, maxCol = min(minCol, s.Col), max(maxCol, s.Col)
	}
	fmt.Printf("playable=%d count=%d row=[%d,%d] col=[%d,%d] tiles=%d\n",
		board.Playable, board.Count, minRow, maxRow, minCol, maxCol,
		len(tiles.Pixels)/assets.MapTileBytes)

	must(os.MkdirAll(out, 0o755))
	write := func(name string, data []byte) { must(os.WriteFile(filepath.Join(out, name), data, 0o644)) }
	b, _ := json.Marshal(map[string]any{
		"squares": squares,
		"rowMin":  minRow, "rowMax": maxRow, "colMin": minCol, "colMax": maxCol,
	})
	write("board.json", b)
	b, _ = json.Marshal(map[string]any{"terrain": layers.Terrain, "objects": layers.Objects})
	write("layers.json", b)
	write("maptiles.bin", tiles.Pixels)
	rgb := make([]byte, 0, 768)
	for _, c := range pal {
		rgb = append(rgb, c.R, c.G, c.B)
	}
	write("palette.bin", rgb)
}
