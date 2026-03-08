/*
Phase 8: Go による高性能キーワードインデックスサービス
=======================================================
なぜ Go を使うのか:
  - Python の FastAPI は GIL（Global Interpreter Lock）により真の並列処理ができない
  - Go の goroutine は数千〜数万の並行処理を少ないメモリで実現できる
  - 転置インデックスの構築など CPU/メモリ集約型の処理に最適

考えてほしい疑問:
  Q1. Goroutine はスレッドと何が違うのか？（コスト: 数KB vs 数MB）
  Q2. channel でデータを受け渡す理由は？（共有メモリの危険性）
  Q3. Go の defer はなぜ便利か？（Java の finally との比較）
  Q4. このサービスを Docker コンテナ化すると、なぜイメージが数MB になるのか？

実行方法:
  go mod init knowledge-ai-search
  go run main.go
  curl "http://localhost:8001/search?q=Python"
*/

package main

import (
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"
	"os"
	"strings"
	"sync"
	"time"
	"unicode"
)

// --- データ構造 ---

// Note はAPIから受け取るノートデータ
type Note struct {
	ID      int    `json:"id"`
	Title   string `json:"title"`
	Content string `json:"content"`
}

// SearchResult は検索結果の1件
type SearchResult struct {
	NoteID   int     `json:"note_id"`
	Title    string  `json:"title"`
	Score    float64 `json:"score"`
	Snippet  string  `json:"snippet"`
}

// InvertedIndex は転置インデックス（単語 → ノートIDリスト）
// [考える] map は並行アクセスで race condition が起きる。なぜ sync.RWMutex が必要か？
type InvertedIndex struct {
	mu    sync.RWMutex
	index map[string][]int  // word → []noteID
	notes map[int]Note      // noteID → Note
}

func NewInvertedIndex() *InvertedIndex {
	return &InvertedIndex{
		index: make(map[string][]int),
		notes: make(map[int]Note),
	}
}

func (idx *InvertedIndex) Add(note Note) {
	idx.mu.Lock()
	defer idx.mu.Unlock()  // [考える] defer がないと何が起きるか？

	idx.notes[note.ID] = note

	// テキストをトークナイズ（単語に分割）
	words := tokenize(note.Title + " " + note.Content)
	for _, word := range words {
		// 重複を避けてノートIDを追加
		if !contains(idx.index[word], note.ID) {
			idx.index[word] = append(idx.index[word], note.ID)
		}
	}
}

func (idx *InvertedIndex) Search(query string) []SearchResult {
	idx.mu.RLock()  // 読み取り専用ロック（複数goroutineが同時に読める）
	defer idx.mu.RUnlock()

	queryWords := tokenize(query)
	if len(queryWords) == 0 {
		return nil
	}

	// スコアリング: クエリ単語のうち何語マッチするか
	scores := make(map[int]int)
	for _, word := range queryWords {
		for _, noteID := range idx.index[word] {
			scores[noteID]++
		}
	}

	var results []SearchResult
	for noteID, score := range scores {
		note := idx.notes[noteID]
		results = append(results, SearchResult{
			NoteID:  noteID,
			Title:   note.Title,
			Score:   float64(score) / float64(len(queryWords)),
			Snippet: extractSnippet(note.Content, query, 100),
		})
	}

	// スコア降順でソート（シンプルなバブルソート - 実際はsort.Sliceを使う）
	// [実装してみよう] sort.Slice を使って書き直す
	for i := 0; i < len(results)-1; i++ {
		for j := i + 1; j < len(results); j++ {
			if results[j].Score > results[i].Score {
				results[i], results[j] = results[j], results[i]
			}
		}
	}

	return results
}

// --- テキスト処理 ---

func tokenize(text string) []string {
	// 小文字化して単語に分割（英語のみ。日本語は別途形態素解析が必要）
	// [実装してみよう] kagome（Go の日本語形態素解析ライブラリ）を組み込む
	text = strings.ToLower(text)
	words := strings.FieldsFunc(text, func(r rune) bool {
		return !unicode.IsLetter(r) && !unicode.IsNumber(r)
	})

	// ストップワード除去（意味のない単語を除く）
	stopWords := map[string]bool{"the": true, "a": true, "is": true, "in": true, "of": true}
	var result []string
	for _, w := range words {
		if len(w) > 1 && !stopWords[w] {
			result = append(result, w)
		}
	}
	return result
}

func extractSnippet(content, query string, maxLen int) string {
	idx := strings.Index(strings.ToLower(content), strings.ToLower(query))
	if idx < 0 {
		if len(content) > maxLen {
			return content[:maxLen] + "..."
		}
		return content
	}
	start := max(0, idx-30)
	end := min(len(content), idx+maxLen)
	return "..." + content[start:end] + "..."
}

func contains(slice []int, val int) bool {
	for _, v := range slice {
		if v == val {
			return true
		}
	}
	return false
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// --- HTTPハンドラー ---

type Server struct {
	index  *InvertedIndex
	logger *slog.Logger
}

func (s *Server) handleSearch(w http.ResponseWriter, r *http.Request) {
	query := r.URL.Query().Get("q")
	if query == "" {
		http.Error(w, `{"error": "クエリパラメータ q が必要です"}`, http.StatusBadRequest)
		return
	}

	start := time.Now()
	results := s.index.Search(query)
	duration := time.Since(start)

	s.logger.Info("search", "query", query, "results", len(results), "duration_ms", duration.Milliseconds())

	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("X-Search-Duration-Ms", fmt.Sprintf("%d", duration.Milliseconds()))
	json.NewEncoder(w).Encode(map[string]any{
		"query":       query,
		"results":     results,
		"total":       len(results),
		"duration_ms": duration.Milliseconds(),
	})
}

func (s *Server) handleIndex(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "POST のみ", http.StatusMethodNotAllowed)
		return
	}

	var note Note
	if err := json.NewDecoder(r.Body).Decode(&note); err != nil {
		http.Error(w, `{"error": "Invalid JSON"}`, http.StatusBadRequest)
		return
	}

	// goroutine でバックグラウンドにインデックス化（ノンブロッキング）
	// [考える] goroutine でエラーが起きたとき、どうハンドリングするか？
	go s.index.Add(note)

	w.WriteHeader(http.StatusAccepted)
	json.NewEncoder(w).Encode(map[string]string{"status": "accepted"})
}

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))

	server := &Server{
		index:  NewInvertedIndex(),
		logger: logger,
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/search", server.handleSearch)
	mux.HandleFunc("/index",  server.handleIndex)
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(map[string]string{"status": "healthy"})
	})

	port := os.Getenv("PORT")
	if port == "" {
		port = "8001"
	}

	logger.Info("Go search service starting", "port", port)
	if err := http.ListenAndServe(":"+port, mux); err != nil {
		logger.Error("Server failed", "error", err)
		os.Exit(1)
	}
}
