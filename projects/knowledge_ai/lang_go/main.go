// =============================================================================
// Go Health Checker — Go の強みを学ぶ教育用アプリ
// =============================================================================
//
// このアプリは Go の主要な特徴を1ファイルで体験できるように設計されています。
// 実際の HTTP 通信は行わず、シミュレーションで並行処理パターンを学びます。
//
// 学習ポイント:
//   1. Goroutine & Channel (fan-out/fan-in)
//   2. Select 文 (timeout, done channel)
//   3. Context (キャンセル, タイムアウト伝播)
//   4. Interface (Checker インターフェース)
//   5. Error handling (カスタムエラー, %w ラップ, errors.Is/As)
//   6. Struct embedding (型の合成)
//   7. Defer (リソースクリーンアップ)
//   8. sync.WaitGroup, sync.Mutex, sync.Once
//   9. Generics (Result[T])
//  10. Table-driven tests パターン (コメントで紹介)
// =============================================================================

package main

import (
	"context"
	"errors"
	"fmt"
	"math/rand"
	"os"
	"os/signal"
	"strings"
	"sync"
	"syscall"
	"time"
)

// =============================================================================
// 1. Generics — Go 1.18+ のジェネリクス
// =============================================================================
// Go のジェネリクスは型パラメータで記述する。Java の <T> に相当。
// 「どんな型の結果でも成功/失敗を統一的に扱える」汎用コンテナ。

// Result[T] は成功値またはエラーを保持するジェネリック型。
// Rust の Result<T, E> や Haskell の Either に近い概念。
type Result[T any] struct {
	Value T     // 成功時の値（T は任意の型）
	Err   error // 失敗時のエラー
}

// IsOK は成功かどうかを返す。
func (r Result[T]) IsOK() bool {
	return r.Err == nil
}

// Unwrap は成功値を返す。失敗時は panic する（教育用）。
func (r Result[T]) Unwrap() T {
	if r.Err != nil {
		panic(fmt.Sprintf("Unwrap on error: %v", r.Err))
	}
	return r.Value
}

// NewOK は成功の Result を作る。
func NewOK[T any](value T) Result[T] {
	return Result[T]{Value: value}
}

// NewErr はエラーの Result を作る。
func NewErr[T any](err error) Result[T] {
	var zero T
	return Result[T]{Value: zero, Err: err}
}

// =============================================================================
// 2. カスタムエラー型 — Go のエラーハンドリング
// =============================================================================
// Go ではエラーは error インターフェースを実装した値。
// - fmt.Errorf("%w", err) でエラーをラップ（チェーン）
// - errors.Is(err, target) でエラーの一致判定
// - errors.As(err, &target) でエラーの型アサーション
//
// Python の例外階層とは異なり、Go は「値としてのエラー」を返す設計。
// try/catch ではなく if err != nil で明示的にハンドリングする。

// ErrTimeout はタイムアウトを表すセンチネルエラー。
// errors.Is() でこのエラーかどうかを判定できる。
var ErrTimeout = errors.New("health check timed out")

// CheckError はヘルスチェック固有のカスタムエラー型。
// Error() メソッドを実装することで error インターフェースを満たす。
type CheckError struct {
	URL     string // チェック対象の URL
	Code    int    // HTTP ステータスコード（シミュレーション）
	Message string // エラーメッセージ
}

// Error は error インターフェースの実装。
func (e *CheckError) Error() string {
	return fmt.Sprintf("check failed for %s (code=%d): %s", e.URL, e.Code, e.Message)
}

// =============================================================================
// 3. Interface — Go のインターフェース
// =============================================================================
// Go のインターフェースは「暗黙的」に実装される（implements キーワード不要）。
// メソッドのシグネチャが一致すれば、自動的にそのインターフェースを満たす。
// これを「構造的部分型付け (structural subtyping)」と呼ぶ。
//
// Java: class Foo implements Bar { ... }
// Go:   type Foo struct{} で Bar のメソッドを定義するだけ

// Checker はヘルスチェッカーのインターフェース。
// Check メソッドを持つ型なら何でも Checker として扱える。
type Checker interface {
	Check(ctx context.Context, url string) Result[HealthResult]
	Name() string // チェッカーの名前
}

// HealthResult はヘルスチェックの結果を表す構造体。
type HealthResult struct {
	URL     string        // チェック対象
	Status  string        // "OK" or "FAIL"
	Latency time.Duration // 応答時間
	Checker string        // 使用したチェッカー名
}

// =============================================================================
// 4. Struct Embedding — 型の合成（継承ではない）
// =============================================================================
// Go にクラス継承はない。代わりに「構造体の埋め込み (embedding)」で
// フィールドとメソッドを合成する。「has-a」関係だが、メソッドが昇格する。
//
// Java: class HTTPChecker extends BaseChecker { ... }
// Go:   type HTTPChecker struct { BaseChecker } （埋め込み）

// BaseChecker は共通のフィールドを持つ基底構造体。
// 他のチェッカーに埋め込んで使う。
type BaseChecker struct {
	timeout time.Duration // チェックのタイムアウト
}

// Timeout は BaseChecker のメソッド。
// 埋め込み先からも直接呼べる（メソッドの昇格）。
func (b *BaseChecker) Timeout() time.Duration {
	return b.timeout
}

// --- HTTPChecker ---

// HTTPChecker は HTTP ベースのヘルスチェッカー（シミュレーション）。
// BaseChecker を埋め込むことで Timeout() メソッドを継承的に使える。
type HTTPChecker struct {
	BaseChecker // 埋め込み: HTTPChecker.Timeout() が使える
}

// NewHTTPChecker は HTTPChecker を生成する。
func NewHTTPChecker(timeout time.Duration) *HTTPChecker {
	return &HTTPChecker{
		BaseChecker: BaseChecker{timeout: timeout},
	}
}

// Name は Checker インターフェースの実装。
func (h *HTTPChecker) Name() string {
	return "HTTP"
}

// Check は Checker インターフェースの実装。
// 実際の HTTP 通信はせず、ランダムな遅延でシミュレーションする。
func (h *HTTPChecker) Check(ctx context.Context, url string) Result[HealthResult] {
	// シミュレーション: 50〜300ms のランダムな遅延
	latency := time.Duration(50+rand.Intn(250)) * time.Millisecond

	// select 文: 複数のチャネル操作を待ち、最初に準備できたものを実行する。
	// ここでは「シミュレーション完了」と「コンテキストキャンセル」を競合させる。
	select {
	case <-time.After(latency):
		// シミュレーション完了
	case <-ctx.Done():
		// コンテキストがキャンセルされた場合
		// fmt.Errorf("%w", ...) でエラーをラップする
		return NewErr[HealthResult](
			fmt.Errorf("%w: %s (checker=%s)", ErrTimeout, url, h.Name()),
		)
	}

	// 20% の確率でエラーをシミュレーション
	if rand.Intn(5) == 0 {
		err := &CheckError{
			URL:     url,
			Code:    503,
			Message: "service unavailable (simulated)",
		}
		// エラーラップ: 元のエラー情報を保持しつつ文脈を追加
		return NewErr[HealthResult](
			fmt.Errorf("HTTP check failed: %w", err),
		)
	}

	return NewOK(HealthResult{
		URL:     url,
		Status:  "OK",
		Latency: latency,
		Checker: h.Name(),
	})
}

// --- TCPChecker ---

// TCPChecker は TCP ベースのヘルスチェッカー（シミュレーション）。
// HTTPChecker と同じ Checker インターフェースを実装する。
type TCPChecker struct {
	BaseChecker // 同じく BaseChecker を埋め込み
}

// NewTCPChecker は TCPChecker を生成する。
func NewTCPChecker(timeout time.Duration) *TCPChecker {
	return &TCPChecker{
		BaseChecker: BaseChecker{timeout: timeout},
	}
}

// Name は Checker インターフェースの実装。
func (t *TCPChecker) Name() string {
	return "TCP"
}

// Check は Checker インターフェースの実装。
// TCP 接続のシミュレーション（HTTP より高速な想定）。
func (t *TCPChecker) Check(ctx context.Context, url string) Result[HealthResult] {
	latency := time.Duration(10+rand.Intn(100)) * time.Millisecond

	select {
	case <-time.After(latency):
		// 完了
	case <-ctx.Done():
		return NewErr[HealthResult](
			fmt.Errorf("%w: %s (checker=%s)", ErrTimeout, url, t.Name()),
		)
	}

	// 10% の確率でエラー
	if rand.Intn(10) == 0 {
		err := &CheckError{
			URL:     url,
			Code:    0,
			Message: "connection refused (simulated)",
		}
		return NewErr[HealthResult](fmt.Errorf("TCP check failed: %w", err))
	}

	return NewOK(HealthResult{
		URL:     url,
		Status:  "OK",
		Latency: latency,
		Checker: t.Name(),
	})
}

// =============================================================================
// 5. HealthCheckService — 並行処理の中心
// =============================================================================
// Goroutine: Go の軽量スレッド。go キーワードで起動。OS スレッドより圧倒的に軽い。
// Channel: Goroutine 間の通信パイプ。「メモリを共有するのではなく、通信でメモリを共有する」
// WaitGroup: 複数の Goroutine の完了を待つカウンター。
// Mutex: 排他制御。共有データへの同時アクセスを防ぐ。
// Once: 一度だけ実行される処理を保証する。

// HealthCheckService は並行ヘルスチェックを管理するサービス。
type HealthCheckService struct {
	checkers []Checker         // 使用するチェッカーのリスト
	mu       sync.Mutex        // stats への排他アクセス用ミューテックス
	stats    map[string]int    // チェッカー別の成功カウント
	once     sync.Once         // 初期化を1回だけ実行
	initMsg  string            // 初期化メッセージ
}

// NewHealthCheckService はサービスを生成する。
func NewHealthCheckService(checkers ...Checker) *HealthCheckService {
	return &HealthCheckService{
		checkers: checkers,
		stats:    make(map[string]int),
	}
}

// init は sync.Once で1回だけ実行される初期化処理。
// 設定ファイル読み込みや DB 接続など、1回だけやりたい処理に使う。
func (s *HealthCheckService) init() {
	s.once.Do(func() {
		s.initMsg = "HealthCheckService initialized"
		fmt.Printf("  [sync.Once] %s\n", s.initMsg)
	})
}

// recordSuccess は成功カウントを安全にインクリメントする。
// sync.Mutex で排他制御し、データ競合 (race condition) を防ぐ。
func (s *HealthCheckService) recordSuccess(checkerName string) {
	s.mu.Lock()         // ロック取得
	defer s.mu.Unlock() // defer: 関数終了時に必ずロック解放（リソースクリーンアップ）
	s.stats[checkerName]++
}

// RunChecks は fan-out/fan-in パターンで並行ヘルスチェックを実行する。
//
// Fan-out/Fan-in パターン:
//   Fan-out: 1つのチャネルから複数の Goroutine (ワーカー) にタスクを配る
//   Fan-in:  複数のワーカーの結果を1つのチャネルに集約する
//
//   [URL1] ──┐                    ┌── [Worker1] ──┐
//   [URL2] ──┤── jobs channel ──> ├── [Worker2] ──┤── results channel ──> [Collector]
//   [URL3] ──┘                    └── [Worker3] ──┘
//
func (s *HealthCheckService) RunChecks(ctx context.Context, urls []string, workerCount int) []Result[HealthResult] {
	// sync.Once で初期化（何回呼ばれても1回だけ実行）
	s.init()

	// --- チャネルの作成 ---
	// チャネルはバッファサイズを指定できる。
	// バッファなし (make(chan T)): 送信と受信が同期する（ブロッキング）
	// バッファあり (make(chan T, n)): n 個まで非同期に送信できる
	jobs := make(chan string, len(urls))       // タスク（URL）を送るチャネル
	results := make(chan Result[HealthResult], len(urls)) // 結果を受け取るチャネル

	// --- Fan-out: ワーカー Goroutine を起動 ---
	// sync.WaitGroup で全ワーカーの完了を追跡する。
	var wg sync.WaitGroup

	for i := 0; i < workerCount; i++ {
		wg.Add(1) // カウンターを +1

		// go キーワードで Goroutine を起動。
		// Goroutine は OS スレッドではなく Go ランタイムが管理する軽量スレッド。
		// 数千〜数百万の Goroutine を同時に動かせる。
		go func(workerID int) {
			// defer: 関数終了時に必ず実行される。
			// panic が起きても defer は実行されるため、リソースクリーンアップに最適。
			defer wg.Done() // カウンターを -1

			// range でチャネルからタスクを受け取るループ。
			// チャネルが close されるとループが終了する。
			for url := range jobs {
				// チェッカーをラウンドロビンで選択
				checker := s.checkers[workerID%len(s.checkers)]

				fmt.Printf("  [Worker %d] checking %s with %s checker\n",
					workerID, url, checker.Name())

				result := checker.Check(ctx, url)

				// 成功時にカウントを記録（Mutex で保護）
				if result.IsOK() {
					s.recordSuccess(checker.Name())
				}

				// 結果をチャネルに送信（Fan-in の入口）
				results <- result
			}
		}(i) // i を引数で渡す（クロージャの変数キャプチャに注意）
	}

	// --- タスクをチャネルに投入 ---
	for _, url := range urls {
		jobs <- url // チャネルに URL を送信
	}
	close(jobs) // 全タスク投入後にチャネルを close（ワーカーの range ループを終了させる）

	// --- 別の Goroutine で全ワーカーの完了を待ち、results を close ---
	go func() {
		wg.Wait()      // 全ワーカーが Done() するまでブロック
		close(results) // 全結果送信後に close（コレクターの range ループを終了させる）
	}()

	// --- Fan-in: 結果を収集 ---
	var collected []Result[HealthResult]
	for result := range results {
		collected = append(collected, result)
	}

	return collected
}

// GetStats は成功カウントのコピーを返す。
func (s *HealthCheckService) GetStats() map[string]int {
	s.mu.Lock()
	defer s.mu.Unlock()

	// マップのコピーを返す（元のマップへの参照を漏らさない）
	copy := make(map[string]int, len(s.stats))
	for k, v := range s.stats {
		copy[k] = v
	}
	return copy
}

// =============================================================================
// 6. 結果表示
// =============================================================================

// printResults は結果をテーブル形式で表示する。
func printResults(results []Result[HealthResult]) {
	fmt.Println()
	fmt.Println(strings.Repeat("=", 75))
	fmt.Printf("  %-35s %-8s %-10s %s\n", "URL", "STATUS", "LATENCY", "CHECKER")
	fmt.Println(strings.Repeat("-", 75))

	okCount := 0
	failCount := 0

	for _, r := range results {
		if r.IsOK() {
			hr := r.Value
			fmt.Printf("  %-35s %-8s %-10s %s\n",
				hr.URL, "OK", hr.Latency.Round(time.Millisecond), hr.Checker)
			okCount++
		} else {
			// --- エラーハンドリングのデモ ---
			status := "FAIL"
			detail := r.Err.Error()

			// errors.Is: エラーチェーンの中に特定のエラーがあるか判定
			if errors.Is(r.Err, ErrTimeout) {
				status = "TIMEOUT"
			}

			// errors.As: エラーチェーンの中から特定の型を取り出す
			var checkErr *CheckError
			if errors.As(r.Err, &checkErr) {
				fmt.Printf("  %-35s %-8s code=%-5d %s\n",
					checkErr.URL, status, checkErr.Code, checkErr.Message)
			} else {
				fmt.Printf("  %-35s %-8s %-10s %s\n",
					"(unknown)", status, "-", detail)
			}
			failCount++
		}
	}

	fmt.Println(strings.Repeat("-", 75))
	fmt.Printf("  Total: %d | OK: %d | FAIL: %d\n", len(results), okCount, failCount)
	fmt.Println(strings.Repeat("=", 75))
}

// =============================================================================
// 7. Graceful Shutdown パターン
// =============================================================================
// OS シグナル (Ctrl+C) を受け取り、Context をキャンセルして
// 全 Goroutine を安全に停止させるパターン。
// 本番の Web サーバーやワーカーで頻出する重要パターン。

// setupGracefulShutdown は SIGINT/SIGTERM を捕捉し、Context をキャンセルする。
func setupGracefulShutdown() (context.Context, context.CancelFunc) {
	// context.WithCancel: キャンセル可能なコンテキストを生成。
	// cancel() を呼ぶと ctx.Done() チャネルが close される。
	ctx, cancel := context.WithCancel(context.Background())

	// OS シグナルを受け取るチャネル
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		select {
		case sig := <-sigCh:
			fmt.Printf("\n  [Signal] %v を受信。シャットダウン中...\n", sig)
			cancel() // Context をキャンセル → 全 Goroutine に伝播
		case <-ctx.Done():
			// 正常終了時
		}
		signal.Stop(sigCh) // シグナル監視を停止
	}()

	return ctx, cancel
}

// =============================================================================
// 8. Table-Driven Tests パターン（コメント解説）
// =============================================================================
// Go のテストは _test.go ファイルに書く。
// Table-driven tests は Go で最も一般的なテストパターン。
//
// 例:
//
//   func TestHTTPChecker_Check(t *testing.T) {
//       // テストケースをスライスで定義（テーブル）
//       tests := []struct {
//           name    string        // テストケース名
//           url     string        // 入力 URL
//           timeout time.Duration // タイムアウト
//           wantErr bool          // エラーを期待するか
//       }{
//           {name: "正常系", url: "https://example.com", timeout: 5 * time.Second, wantErr: false},
//           {name: "タイムアウト", url: "https://slow.example.com", timeout: 1 * time.Nanosecond, wantErr: true},
//           {name: "空URL", url: "", timeout: 5 * time.Second, wantErr: true},
//       }
//
//       for _, tt := range tests {
//           // t.Run でサブテストを実行（テスト名が表示される）
//           t.Run(tt.name, func(t *testing.T) {
//               checker := NewHTTPChecker(tt.timeout)
//               ctx, cancel := context.WithTimeout(context.Background(), tt.timeout)
//               defer cancel()
//
//               result := checker.Check(ctx, tt.url)
//               if (result.Err != nil) != tt.wantErr {
//                   t.Errorf("Check() error = %v, wantErr = %v", result.Err, tt.wantErr)
//               }
//           })
//       }
//   }
//
// 実行: go test -v -run TestHTTPChecker_Check

// =============================================================================
// 9. Main — すべてを組み合わせる
// =============================================================================

func main() {
	fmt.Println()
	fmt.Println("  ============================================")
	fmt.Println("  Go Concurrent Health Checker")
	fmt.Println("  ============================================")
	fmt.Println()

	// --- Graceful Shutdown の設定 ---
	// Ctrl+C で安全にシャットダウンするための Context を準備
	ctx, cancel := setupGracefulShutdown()
	defer cancel() // main 終了時に必ずキャンセル

	// --- Context にタイムアウトを追加 ---
	// context.WithTimeout: 指定時間後に自動キャンセルされる Context を生成。
	// 親 Context (graceful shutdown) がキャンセルされても子もキャンセルされる。
	// Context はツリー構造で、キャンセルは親から子へ伝播する。
	ctx, timeoutCancel := context.WithTimeout(ctx, 10*time.Second)
	defer timeoutCancel()

	// --- チェック対象の URL リスト ---
	urls := []string{
		"https://api.example.com/health",
		"https://db.example.com:5432",
		"https://cache.example.com:6379",
		"https://auth.example.com/status",
		"https://queue.example.com:5672",
		"https://storage.example.com/ping",
		"https://search.example.com:9200",
		"https://monitor.example.com/health",
	}

	// --- Checker インターフェースのポリモーフィズム ---
	// HTTPChecker と TCPChecker は同じ Checker インターフェースを実装。
	// サービスは具体的な型を知らずに、インターフェース経由で利用できる。
	httpChecker := NewHTTPChecker(5 * time.Second)
	tcpChecker := NewTCPChecker(3 * time.Second)

	// 埋め込みメソッドのデモ: BaseChecker.Timeout() が直接呼べる
	fmt.Printf("  HTTP Checker timeout: %v\n", httpChecker.Timeout())
	fmt.Printf("  TCP  Checker timeout: %v\n", tcpChecker.Timeout())
	fmt.Println()

	// --- サービスの生成と実行 ---
	service := NewHealthCheckService(httpChecker, tcpChecker)

	fmt.Println("  --- ヘルスチェック開始 (worker=3) ---")
	fmt.Println()

	start := time.Now()
	results := service.RunChecks(ctx, urls, 3)
	elapsed := time.Since(start)

	// --- 結果表示 ---
	printResults(results)

	// --- 統計情報 ---
	stats := service.GetStats()
	fmt.Println()
	fmt.Println("  [Stats] チェッカー別成功数:")
	for name, count := range stats {
		fmt.Printf("    %s: %d\n", name, count)
	}

	fmt.Printf("\n  全チェック完了: %v\n", elapsed.Round(time.Millisecond))

	// --- Generics のデモ ---
	fmt.Println()
	fmt.Println("  --- Generics デモ ---")
	demonstrateGenerics()

	fmt.Println()
	fmt.Println("  Ctrl+C を押すと graceful shutdown のデモも確認できます。")
	fmt.Println()
}

// demonstrateGenerics は Result[T] の汎用性を示す。
// 同じ Result 型で異なる型パラメータ (string, int) を使える。
func demonstrateGenerics() {
	// Result[string]
	strResult := NewOK("hello, generics!")
	fmt.Printf("  Result[string]: value=%q, ok=%v\n", strResult.Unwrap(), strResult.IsOK())

	// Result[int]
	intResult := NewOK(42)
	fmt.Printf("  Result[int]:    value=%d,          ok=%v\n", intResult.Unwrap(), intResult.IsOK())

	// Result[int] with error
	errResult := NewErr[int](fmt.Errorf("something went wrong"))
	fmt.Printf("  Result[int]:    err=%q, ok=%v\n", errResult.Err, errResult.IsOK())
}
