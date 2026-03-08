/*
Search Service - Go による全文検索サービス
==========================================
[BUG-07] マップへの並行アクセスで race condition が存在する
         → 同時リクエストで panic: concurrent map read and map write

修正方法: sync.RWMutex を追加する
  mu.Lock() / mu.Unlock() でWrite操作を保護
  mu.RLock() / mu.RUnlock() でRead操作を保護

[BUG-08] インデックスがメモリのみ → サービス再起動でデータが消える
         修正方法: Redis または BadgerDB で永続化する
*/

package main

import (
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"
	"os"
	"strings"
	// "sync"  // ★ [BUG-07] ここをアンコメントしてmutexを追加するのが修正 ★
)

type Note struct {
	ID      int    `json:"id"`
	Title   string `json:"title"`
	Content string `json:"content"`
}

type SearchResult struct {
	NoteID  int     `json:"note_id"`
	Title   string  `json:"title"`
	Score   float64 `json:"score"`
	Snippet string  `json:"snippet"`
}

// ★ [BUG-07] mu sync.RWMutex がない → 並行アクセスで race condition ★
// 修正: mu sync.RWMutex フィールドを追加して全操作でLockを取る
type InvertedIndex struct {
	// mu    sync.RWMutex  ← ここをアンコメントして使う
	index map[string][]int
	notes map[int]Note
}

func NewIndex() *InvertedIndex {
	return &InvertedIndex{
		index: make(map[string][]int),
		notes: make(map[int]Note),
	}
}

func (idx *InvertedIndex) Add(note Note) {
	// ★ 修正時はここに idx.mu.Lock() / defer idx.mu.Unlock() を追加 ★
	idx.notes[note.ID] = note
	for _, word := range tokenize(note.Title + " " + note.Content) {
		if !containsInt(idx.index[word], note.ID) {
			idx.index[word] = append(idx.index[word], note.ID)
		}
	}
}

func (idx *InvertedIndex) Search(query string) []SearchResult {
	// ★ 修正時はここに idx.mu.RLock() / defer idx.mu.RUnlock() を追加 ★
	words := tokenize(query)
	scores := make(map[int]int)
	for _, word := range words {
		for _, nid := range idx.index[word] {
			scores[nid]++
		}
	}
	var results []SearchResult
	for nid, score := range scores {
		note := idx.notes[nid]
		results = append(results, SearchResult{
			NoteID:  nid,
			Title:   note.Title,
			Score:   float64(score) / float64(len(words)),
			Snippet: snippet(note.Content, query, 80),
		})
	}
	return results
}

func tokenize(text string) []string {
	text = strings.ToLower(text)
	var words []string
	for _, w := range strings.Fields(text) {
		w = strings.Trim(w, ".,!?;:\"'()")
		if len(w) > 2 {
			words = append(words, w)
		}
	}
	return words
}

func snippet(content, query string, maxLen int) string {
	idx := strings.Index(strings.ToLower(content), strings.ToLower(query))
	if idx < 0 {
		if len(content) > maxLen {
			return content[:maxLen] + "..."
		}
		return content
	}
	start := idx - 20
	if start < 0 {
		start = 0
	}
	end := start + maxLen
	if end > len(content) {
		end = len(content)
	}
	return "..." + content[start:end] + "..."
}

func containsInt(s []int, v int) bool {
	for _, x := range s {
		if x == v {
			return true
		}
	}
	return false
}

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	idx := NewIndex()

	mux := http.NewServeMux()

	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(map[string]string{"status": "ok", "service": "search_service"})
	})

	// メトリクス（簡易版 - Phase 6 で Prometheus client に置き換える）
	mux.HandleFunc("/metrics", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintf(w, "# search_service metrics\nsearch_index_size %d\n", len(idx.notes))
	})

	mux.HandleFunc("/index", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "POST only", http.StatusMethodNotAllowed)
			return
		}
		var note Note
		if err := json.NewDecoder(r.Body).Decode(&note); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
		// ★ goroutineでバックグラウンド処理 → [BUG-07]の race condition が発生する場所 ★
		go idx.Add(note)  // 複数の goroutine が同時に idx.Add を呼ぶと panic する

		w.WriteHeader(http.StatusAccepted)
		json.NewEncoder(w).Encode(map[string]string{"status": "accepted"})
		logger.Info("note indexed", "note_id", note.ID)
	})

	mux.HandleFunc("/search", func(w http.ResponseWriter, r *http.Request) {
		q := r.URL.Query().Get("q")
		if q == "" {
			http.Error(w, `{"error":"q is required"}`, http.StatusBadRequest)
			return
		}
		results := idx.Search(q)
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]any{
			"query":   q,
			"results": results,
			"total":   len(results),
		})
	})

	port := os.Getenv("PORT")
	if port == "" {
		port = "8002"
	}
	logger.Info("Search service starting", "port", port)
	if err := http.ListenAndServe(":"+port, mux); err != nil {
		logger.Error("server error", "err", err)
		os.Exit(1)
	}
}
